import glob
import json
import os
from tempfile import NamedTemporaryFile
from typing import Dict, List

import pandas as pd
import PyPDF2
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATE_DIR = os.path.join(STATIC_DIR, "templates")
CSS_DIR = os.path.join(STATIC_DIR, "css")
LOCALES_DIR = os.path.join(STATIC_DIR, "locales")


class ExamSheetGenerator:
    """
    A class for generating exam sheets.
    """

    def __init__(
        self,
        date: str,
        semester: str,
        exam_name: str,
        examiners: List[str],
        university_name: str,
        department_name: str,
        degree_program: str,
        language="en",
        hashcode_num_blocks: int = 3,
        hashcode_block_size: int = 4,
    ) -> None:
        """
        Initializes an instance of the ExamSheetGenerator class.

        Args:
            date (str): The date of the exam.
            semester (str): The semester in which the exam is being conducted.
            exam_name (str): The name of the exam.
            examiners (List[str]): A list of examiners.
            university_name (str): The name of the university.
            department_name (str): The name of the department.
            degree_program (str): The degree program.
            language (str, optional): The language of the exam sheet. Defaults to "en".
            hashcode_num_blocks (int, optional): The number of blocks in the hashcode.
                Defaults to 3.
            hashcode_block_size (int, optional): The size of each block in the hashcode.
                Defaults to 4.
        """
        self.env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        self.template = self.env.get_template("exam_sheet.html")
        self.exam_info = {
            "date": date,
            "semester": semester,
            "exam_name": exam_name,
            "examiners": examiners,
            "degree_program": degree_program,
            "university_name": university_name,
            "department_name": department_name,
            "hashcode_num_blocks": hashcode_num_blocks,
            "hashcode_block_size": hashcode_block_size,
        }
        self.language = language

    def get_css(self) -> str:
        """
        Returns the CSS content for the exam sheet.

        Returns:
            str: The CSS content.
        """
        css_files = glob.glob(os.path.join(CSS_DIR, "*.css"))
        format_specific_css_files = glob.glob(os.path.join(CSS_DIR, "*.css"))
        css_files.extend(format_specific_css_files)
        css_content = ""
        for css_file in css_files:
            with open(css_file, "r") as f:
                css_content += "\n" + f.read()
        return css_content

    def load_labels(self, language: str) -> Dict[str, str]:
        """
        Loads the labels for the specified language.

        Args:
            language (str): The language for which to load labels.

        Returns:
            Dict[str, str]: A dictionary containing the labels.
        """
        labels_file = os.path.join(LOCALES_DIR, f"labels_{language}.json")
        if not os.path.exists(labels_file):
            raise FileNotFoundError(f"Labels file for language '{language}' not found.")
        with open(labels_file, "r") as f:
            labels_content = f.read()
        labels = json.loads(labels_content)
        return labels

    def generate_pdf(
        self,
        students: pd.DataFrame,
        output_file: str,
        separate_file_per_room: bool = False,
    ) -> None:
        """
        Generates a PDF exam sheet for the given students.

        Args:
            students (pd.DataFrame): A DataFrame containing the student information.
            output_file (str): The path to the output PDF file.
            separate_file_per_room (bool, optional): If True, creates a separate PDF file
                for each room with suffix "_room.pdf". If False, merges all rooms into
                a single PDF file. Defaults to False.

        Returns:
            None
        """
        if separate_file_per_room:
            # Create separate PDF for each room
            base_name = output_file.rsplit(".", 1)[0] if "." in output_file else output_file
            for room, group in students.groupby("room"):
                room_students = group.reset_index(drop=True)
                room_output_file = f"{base_name}_{room}.pdf"
                self.generate_room_pdf(str(room), room_students, room_output_file)
        else:
            # Create all room PDFs as temp files and merge them
            merger = PyPDF2.PdfWriter()
            temp_file_contexts = []

            try:
                # Create all temporary files with context managers
                for room, group in students.groupby("room"):
                    room_students = group.reset_index(drop=True)
                    temp_file = NamedTemporaryFile(suffix=f"_{room}.pdf", delete=False)
                    temp_file_contexts.append(temp_file)

                    with temp_file:
                        self.generate_room_pdf(str(room), room_students, temp_file.name)
                        merger.append(temp_file.name)

                # Write the merged PDF to the output file
                with open(output_file, "wb") as output_pdf:
                    merger.write(output_pdf)

            finally:
                # Clean up temporary files
                for temp_file in temp_file_contexts:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)

    def _generate_supervision_list(
        self,
        room: str,
        students: pd.DataFrame,
        output_file: str,
    ) -> None:
        """
        Generates a supervision list for the given students.

        Args:
            room (str): The room for which the supervision list is generated.
            students (List[Dict[str, str]]): A list of dictionaries containing the
                student information.
            output_file (str): The path to the output file.
        """
        html = self.env.get_template("supervision_list.html").render(
            students=students.to_dict("records"),
            exam_info=self.exam_info,
            labels=self.load_labels(self.language),
            room=room,
        )
        HTML(string=html).write_pdf(output_file)

    def _generate_exam_sheets(
        self,
        room: str,
        students: pd.DataFrame,
        output_file: str,
        add_empty_page: bool = False,
    ) -> None:
        """
        Generates exam sheets for the given students.
        Args:
            room (str): The room for which the exam sheets are generated.
            students (List[Dict[str, str]]): A list of dictionaries containing the
                student information.
            output_file (str): The path to the output file.
            add_empty_page (bool, optional): Whether to add an empty page at the beginning.
                Defaults to False.
        """
        html = self.env.get_template("exam_sheet.html").render(
            students=students.to_dict("records"),
            room=room,
            exam_info=self.exam_info,
            labels=self.load_labels(self.language),
            css=self.get_css(),
            add_empty_page=add_empty_page,
        )
        HTML(string=html).write_pdf(output_file)

    def generate_room_pdf(
        self,
        room: str,
        students: pd.DataFrame,
        output_file: str,
    ) -> None:
        """
        Generates a PDF exam sheet for the given room and students.
        This sheet includes both the supervision list and the exam sheet.

        Args:
            room (str): The room for which the exam sheet is generated.
            students (List[Dict[str, str]]): A list of dictionaries containing the
                student information.
            output_file (str): The path to the output PDF file.
            add_empty_page (bool, optional): Whether to add an empty page at the beginning.
                Defaults to False.
        """
        with NamedTemporaryFile(suffix=".pdf") as f1, NamedTemporaryFile(suffix=".pdf") as f2:
            supervision_pdf = f1.name
            sheet_pdf = f2.name

            # Generate the supervision list for the room
            self._generate_supervision_list(room, students, supervision_pdf)

            # Check if we need to add an empty page.
            # If the number of pages in the supervision PDF is odd, we add an empty page
            n_pages = len(PyPDF2.PdfReader(supervision_pdf).pages)
            should_add_empty_page = n_pages % 2 == 1

            # Generate the exam sheet for the room
            self._generate_exam_sheets(
                room, students, sheet_pdf, add_empty_page=should_add_empty_page
            )

            # Merge the two PDFs
            merger = PyPDF2.PdfWriter()
            merger.append(supervision_pdf)
            merger.append(sheet_pdf)

            # Write the merged PDF to the output file
            with open(output_file, "wb") as output_pdf:
                merger.write(output_pdf)
