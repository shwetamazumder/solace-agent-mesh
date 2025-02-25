"""Create a new file in file service"""

from solace_ai_connector.common.log import log
from ....common.action import Action
from ....common.action_response import ActionResponse
from ....services.file_service import FS_PROTOCOL, FileService
from ....services.file_service.file_utils import starts_with_fs_url


class CreateFile(Action):
    """Action to create a new file in file service"""

    def __init__(self, **kwargs):

        super().__init__(
            {
                "name": "create_file",
                "prompt_directive": f"Creates a new persisted file and returns the file block with {FS_PROTOCOL} URL",
                "params": [
                    {
                        "name": "name",
                        "desc": "File name (required) - must have an extension. Eg: file.csv",
                        "type": "string",
                    },
                    {
                        "name": "content",
                        "desc": "Content of the file (required)",
                        "type": "string",
                    },
                ],
                "required_scopes": ["global:create_file:write"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        name: str = params.get("name")
        content: str = params.get("content")
        session_id: str = meta.get("session_id")

        if not name or not content:
            return ActionResponse(message="Error: name and content are required.")

        try:
            # Upload the file
            file_service = FileService()

            updated_content = content
            if starts_with_fs_url(updated_content):
                updated_content = file_service.resolve_url(updated_content, session_id)
            else:
                updated_content = file_service.resolve_all_resolvable_urls(updated_content, session_id)

            if isinstance(updated_content, str):
                updated_content = updated_content.encode("utf-8")

            file_meta = file_service.upload_from_buffer(
                updated_content,
                name,
                session_id,
                data_source="Global Agent - Create File Action",
            )
        except Exception as e:
            log.error("Failed to upload file %s: %s", name, str(e))
            return ActionResponse(message=f"Failed to upload the file: {name}")

        file_block = file_service.get_file_block_by_metadata(file_meta)
        return ActionResponse(
            message=f"Following file has been created:\n\n{file_block}",
        )
