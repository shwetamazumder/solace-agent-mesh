"""Action description"""

from solace_ai_connector.common.log import log
from markitdown import MarkItDown
from markitdown import UnsupportedFormatException
import json
import os
import mimetypes
import tempfile
from ....common.action import Action
from ....common.action_response import ActionResponse
from ....services.file_service import FS_PROTOCOL, FileService

STRIP_LENGTH = len(FS_PROTOCOL) + len("://") + 36 + 1  # 36 is uuid, 1 is underscore


class ConvertFileToMarkdown(Action):

    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "convert_file_to_markdown",
                "prompt_directive": (
                    "Convert various file formats to Markdown using the MarkItDown utility. "
                    "Supported file types include PDF, Word, Excel, HTML, CSV and PPTX "
                    "and ZIP files. Files are provided in "
                    + f"{FS_PROTOCOL}://"
                    + " format. "
                    "JSON and XML files are not supported. "
                    "This action will return Markdown files."
                ),
                "params": [
                    {
                        "name": "files",
                        "desc": (
                            f"List of {FS_PROTOCOL}:// URLs to the files to convert to Markdown. "
                            f"For example: ['{FS_PROTOCOL}://file1.pdf', '{FS_PROTOCOL}://file2.docx']"
                        ),
                        "type": "array",
                    }
                ],
                "required_scopes": ["global:markitdown:execute"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        files = params.get("files", [])
        session_id = meta.get("session_id")
        log.debug("Doing markitdown convert action: %s", params["files"])

        if isinstance(files, str):
            try:
                files = json.loads(files)
            except json.JSONDecodeError:
                log.error("Failed to decode files string as JSON")
                return ActionResponse(message="Error: File URL list is not valid.")

        return self.do_action(files, session_id)

    def extract_file_format(self, file_path: str) -> str:
        """
        Extracts the file format from a file path or guesses it using mimetypes if not present.
        """
        file_extension = os.path.splitext(file_path)[1]
        if file_extension:
            return file_extension.lower()

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            guessed_extension = mimetypes.guess_extension(mime_type)
            if guessed_extension:
                return guessed_extension.lower()

        raise ValueError(f"Unable to determine file format for path: {file_path}")

    def do_action(self, files, session_id) -> ActionResponse:
        markitdown_client = MarkItDown()
        file_service = FileService()

        response_messages = []
        uploaded_files = []

        # Iterate over each file URL
        for file_url in files:
            try:
                file_buffer = file_service.download_to_buffer(file_url, session_id)
            except Exception as e:
                log.error(
                    "Failed to download file from the url %s: %s", file_url, str(e)
                )
                response_messages.append(
                    f"Failed to download file from the url {file_url}"
                )
                continue

            # Find the file extension
            try:
                file_extension = self.extract_file_format(file_url)
            except ValueError:
                response_messages.append(
                    f"Could not determine file format for: {file_url}"
                )
                continue

            # strip first {STRIP LENGTH} characters of the url to get the original name
            original_name = file_url[STRIP_LENGTH:]

            with tempfile.NamedTemporaryFile(
                delete=True, suffix=file_extension
            ) as temporary_file:
                try:
                    # Write to temp file
                    temporary_file.write(file_buffer)
                    temporary_file.flush()

                    # Convert the file to Markdown
                    try:
                        conversion_result = markitdown_client.convert(
                            temporary_file.name
                        )
                        # Empty content
                        if not conversion_result.text_content:
                            log.error("Error converting file %s: Conversion resulted in empty content", file_url)
                            response_messages.append(f"Could not convert file: {file_url} - conversion resulted in empty content")
                            continue
                    except UnsupportedFormatException as e:
                        log.error("Error converting file %s: %s", file_url, str(e))
                        response_messages.append(
                            f"Could not convert file: {file_url} as this format is not supported: {str(e)}"
                        )
                        continue

                    # Use the original file name + "_converted" affix + .md extension
                    converted_filename = f"{original_name}_converted.md"

                    # Upload the converted content
                    file_obj = file_service.upload_from_buffer(
                        conversion_result.text_content.encode("utf-8"),
                        converted_filename,
                        session_id,
                        data_source="Global Agent - MarkItDown Action",
                    )

                    filename = file_obj["name"]
                    uploaded_files.append(file_obj)
                    response_messages.append(f"File converted successfully: {filename}")

                except Exception as e:
                    log.error(
                        "Failed to upload file %s: %s", converted_filename, str(e)
                    )
                    response_messages.append(
                        f"Failed to upload file {converted_filename}"
                    )
                    continue

        return ActionResponse(
            message="\n".join(response_messages), files=uploaded_files
        )
