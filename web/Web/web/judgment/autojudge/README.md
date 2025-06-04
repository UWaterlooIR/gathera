# Auto-Judge Module

This module provides LLM-based automatic document relevance assessment for the Gathera system.

## Structure

```
autojudge/
├── __init__.py          # Module initialization
├── llm.py               # Main LLM integration and judgment logic
├── prompts.py           # Prompt management using Jinja2
├── config.py            # Configuration management
├── prompts/             # Jinja2 prompt templates
│   ├── system_prompt.j2      # Default system prompt
│   ├── user_prompt.j2        # Default user prompt
│   └── user_prompt_strict.j2 # Strict evaluation prompt
└── .env.example         # Example environment variables
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install openai jinja2
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to your project's `.env` file and set:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Optional Configuration**:
   You can customize the LLM behavior with these environment variables:
   - `AUTOJUDGE_MODEL`: OpenAI model to use (default: gpt-4-turbo-preview)
   - `AUTOJUDGE_TEMPERATURE`: Temperature for responses (default: 0.3)
   - `AUTOJUDGE_MAX_TOKENS`: Max tokens for response (default: 500)
   - `AUTOJUDGE_USER_PROMPT`: User prompt template (default: user_prompt.j2)
   - `AUTOJUDGE_SYSTEM_PROMPT`: System prompt template (default: system_prompt.j2)

## Usage

The module is integrated with the Django views and can be accessed through:

1. **Web Interface**: Click the "Judge" button in the Auto Judge section of the document modal
2. **API Endpoint**: POST to `/judgment/post_auto_judgment/` with:
   ```json
   {
     "doc_id": "document_id",
     "doc_title": "Document Title",
     "doc_search_snippet": "Document snippet or content"
   }
   ```

## Response Format

The auto judgment returns:
```json
{
  "doc_id": "document_id",
  "message": "Your auto judgment on document_id has been received",
  "llm_output": "Full LLM response text",
  "judgment": "highly_relevant|relevant|not_relevant",
  "confidence": 0.85,
  "reasoning": "Explanation of the judgment",
  "tokens_used": 250,
  "model": "gpt-4-turbo-preview",
  "llm_error": null
}
```

## Customizing Prompts

To create custom prompts:

1. Add new Jinja2 templates to the `prompts/` directory
2. Use the naming convention:
   - System prompts: `system_prompt_<name>.j2`
   - User prompts: `user_prompt_<name>.j2`
3. Reference them in your configuration or pass the template name when calling the judgment functions

## Error Handling

The module handles various error cases:
- Missing OpenAI API key
- API request failures
- Invalid document data
- Parsing errors

Errors are logged and returned in the `llm_error` field of the response.