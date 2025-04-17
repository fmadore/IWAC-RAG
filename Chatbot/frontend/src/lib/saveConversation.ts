// Type definitions mirroring those in +page.svelte for clarity
interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	isError?: boolean;
	query_time?: number;
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
	.user { 
		background-color: #e1f5fe; 
		text-align: right; 
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
		htmlContent += `<p>${escapeHtml(message.content)}</p>`;
		if (message.role === 'assistant' && message.query_time !== undefined) {
			htmlContent += `<p class="meta">Query Time: ${message.query_time.toFixed(2)}s</p>`;
		}
		if (message.isError) {
			htmlContent += `<p class="meta error">Error occurred</p>`;
		}
		htmlContent += `</div>`;
	});

	if (lastSources && lastSources.length > 0) {
		htmlContent += `
		<div class="sources-section">
			<h2 class="sources-title">Sources for Last Response</h2>
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
						href="${escapeHtml(source.url && source.url.trim() !== '' ? source.url : `https://islam.zmo.de/s/afrique_ouest/item/${source.id}`)}" 
						target="_blank" 
						rel="noopener noreferrer" 
						class="source-link"
					>
						${source.url && source.url.trim() !== '' ? 'View Original Source' : `View on ZMO Database (ID: ${source.id})`}
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
