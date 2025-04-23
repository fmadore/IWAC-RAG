// Type definitions mirroring those in +page.svelte for clarity
interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	isError?: boolean;
	query_time?: number;
	prompt_token_count?: number;
	answer_token_count?: number;
}

interface Source {
	id: string;
	title: string;
	newspaper?: string;
	date?: string;
	text_snippet: string;
	url?: string;
}

// Function to generate basic CSS for the saved HTML file
function getConversationStyles(): string {
	return `body { 
		font-family: sans-serif; 
		line-height: 1.6; 
		margin: 20px; 
		background-color: #f9f9f9; 
		color: #333;
	}
	.container { 
		max-width: 800px; 
		margin: 0 auto; 
		background-color: #fff; 
		padding: 20px; 
		border-radius: 8px; 
		box-shadow: 0 2px 5px rgba(0,0,0,0.1);
	}
	.message { 
		margin-bottom: 15px; 
		padding: 10px 15px; 
		border-radius: 8px; 
		word-wrap: break-word;
	}
	.message h4 {
		margin-top: 0;
		margin-bottom: 8px;
		font-size: 0.9em;
		font-weight: bold;
		color: #555;
	}
	.message p {
		margin-top: 0;
		margin-bottom: 0.5em; /* Add space between paragraphs */
	}
	.message p:last-child {
		margin-bottom: 0;
	}
	.user { 
		background-color: #e1f5fe; 
		margin-left: 40px; 
	}
	.assistant { 
		background-color: #f1f8e9; 
		margin-right: 40px; 
	}
	.error { 
		background-color: #ffebee; 
		border: 1px solid #e57373; 
	}
	.meta { 
		font-size: 0.8em; 
		color: #666; 
		margin-top: 5px; 
	}
	.sources-section { 
		margin-top: 30px; 
		padding-top: 20px; 
		border-top: 1px solid #eee; 
	}
	.sources-title { 
		font-size: 1.2em; 
		font-weight: bold; 
		margin-bottom: 10px; 
	}
	.source-item { 
		margin-bottom: 15px; 
		padding: 10px; 
		border: 1px solid #ddd; 
		border-radius: 5px; 
		background-color: #fff; 
	}
	.source-title { 
		font-weight: bold; 
		margin-bottom: 5px; 
	}
	.source-meta { 
		font-size: 0.9em; 
		color: #555; 
		margin-bottom: 5px; 
	}
	.source-snippet { 
		font-style: italic; 
		color: #666; 
		margin-bottom: 5px; 
	}
	.source-link { 
		font-size: 0.9em; 
		color: #0277bd; 
		text-decoration: none; 
	}
	.source-link:hover { 
		text-decoration: underline; 
	}
	`;
}

// Function to escape HTML characters
function escapeHtml(unsafe: string): string {
	if (!unsafe) return '';
	return unsafe
		 .replace(/&/g, "&amp;")
		 .replace(/</g, "&lt;")
		 .replace(/>/g, "&gt;")
		 .replace(/"/g, "&quot;")
		 .replace(/'/g, "&#039;");
}

// Main function to generate HTML and trigger download
export function saveConversationAsHtml(messages: ChatMessage[], lastSources: Source[]): void {
	if (typeof window === 'undefined') {
		console.error("Save function can only be called in a browser environment.");
		return;
	}

	let htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>IWAC Chat Conversation</title>
	<style>
		${getConversationStyles()}
	</style>
</head>
<body>
	<div class="container">
		<h1>IWAC Chat Conversation</h1>
	`;

	messages.forEach(message => {
		const roleClass = message.role;
		const errorClass = message.isError ? ' error' : '';
		htmlContent += `<div class="message ${roleClass}${errorClass}">`;

		// Add heading based on role
		if (message.role === 'user') {
			htmlContent += `<h4>Question:</h4>`;
		} else if (message.role === 'assistant') {
			htmlContent += `<h4>Answer:</h4>`;
		}

		// Process content for paragraphs
		if (message.content) {
			const escapedContent = escapeHtml(message.content);
			const paragraphs = escapedContent.split('\n\n'); // Split by double newline
			paragraphs.forEach(para => {
				if (para.trim()) { // Avoid empty paragraphs
					// Replace single newlines within a paragraph with <br> for line breaks
					const formattedPara = para.replace(/\n/g, '<br>'); 
					htmlContent += `<p>${formattedPara}</p>`;
				}
			});
		} else if (message.isError) {
			htmlContent += `<p><i>An error occurred.</i></p>`;
		} else {
			htmlContent += `<p><i>No content.</i></p>`;
		}
		
		if (message.role === 'assistant' && (message.query_time !== undefined || message.prompt_token_count !== undefined || message.answer_token_count !== undefined)) {
			htmlContent += `<p class="meta">`;
			if (message.query_time !== undefined) {
				htmlContent += `Query Time: ${message.query_time.toFixed(2)}s`;
			}
			if (message.query_time !== undefined && (message.prompt_token_count !== undefined || message.answer_token_count !== undefined)) {
				htmlContent += ` | `;
			}
			if (message.prompt_token_count !== undefined) {
				htmlContent += `Prompt Tokens: ${message.prompt_token_count}`;
			}
			if (message.prompt_token_count !== undefined && message.answer_token_count !== undefined) {
				htmlContent += ` | `;
			}
			if (message.answer_token_count !== undefined) {
				htmlContent += `Answer Tokens: ${message.answer_token_count}`;
			}
			htmlContent += `</p>`;
		}
		if (message.isError && message.role !== 'assistant') { // Avoid duplicating error message if already shown
			htmlContent += `<p class="meta error">Error occurred</p>`;
		}
		htmlContent += `</div>`;
	});

	if (lastSources && lastSources.length > 0) {
		htmlContent += `
		<div class="sources-section">
			<h2 class="sources-title">Sources for Last Response (${lastSources.length})</h2>
			${lastSources.map(source => `
				<div class="source-item">
					<h3 class="source-title">${escapeHtml(source.title)}</h3>
					<p class="source-meta">
						${source.newspaper ? escapeHtml(source.newspaper) : ''}
						${source.newspaper && source.date ? ', ' : ''}
						${source.date ? escapeHtml(source.date) : ''}
					</p>
					<p class="source-snippet">"${escapeHtml(source.text_snippet)}"</p>
					<a 
						href="${escapeHtml(source.url && source.url.trim() !== '' ? source.url : `https://islam.zmo.de/s/afrique_ouest/item/${source.id.split('_').pop()}`)}" 
						target="_blank" 
						rel="noopener noreferrer" 
						class="source-link"
					>
						${source.url && source.url.trim() !== '' ? 'View Original Source' : `View on Collection Islam Afrique de l'Ouest (ID: ${source.id})`}
					</a>
				</div>
			`).join('')}
		</div>
		`;
	}

	htmlContent += `
	</div>
</body>
</html>
`;

	// Create a Blob and trigger download
	const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	// Create a filename with timestamp
	const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
	link.download = `iwac-chat-conversation-${timestamp}.html`;
	
	// Append to body, click, and remove
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url); // Clean up blob URL
}
