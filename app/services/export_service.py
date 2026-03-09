import zipfile
import io
from pathlib import Path

import openpyxl
from sqlalchemy.orm import Session

from app.models.part import Part
from app.models.measurement import Measurement


def export_parts_to_zip(session: Session, output_path: str) -> str:
    """
    Export all parts to a ZIP archive containing one .xlsx file per part.
    Each .xlsx file has a separate sheet per template parameter, with two
    columns: "Часы наработки" and "Значение", sorted by hours ascending.

    Returns the path to the created ZIP file.
    """
    output_path = str(output_path)
    parts = session.query(Part).all()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for part in parts:
            wb = openpyxl.Workbook()
            # Remove default sheet
            default_sheet = wb.active
            wb.remove(default_sheet)

            for param in part.template.parameters:
                sheet_name = param.name[:31]  # Excel limit
                ws = wb.create_sheet(title=sheet_name)
                ws.append(["Часы наработки", "Значение"])

                measurements = (
                    session.query(Measurement)
                    .filter(
                        Measurement.part_id == part.id,
                        Measurement.parameter_id == param.id,
                    )
                    .order_by(Measurement.hours)
                    .all()
                )
                for m in measurements:
                    ws.append([m.hours, m.value])

            # Determine filename
            if part.serial_number:
                filename = f"{part.serial_number}_{part.name}.xlsx"
            else:
                filename = f"{part.id}_{part.name}.xlsx"

            # Write workbook to buffer and add to zip
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            zf.writestr(filename, buf.read())

    return output_path
