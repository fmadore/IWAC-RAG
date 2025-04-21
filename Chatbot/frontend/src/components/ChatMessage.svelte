<script>
  // Props: message (object with role: 'user'|'assistant', content: string, isError?: boolean, query_time?: number)
  export let message;
  // Avatars (could be replaced with real images)
  const userAvatar = '🧑';
  const assistantAvatar = '🤖';
</script>

<div class="chat-message-container {message.role}">
  {#if message.role === 'assistant'}
    <div class="avatar assistant-avatar">
      {assistantAvatar}
    </div>
  {/if}
  <div 
    class="message-bubble {message.role} {message.isError ? 'error' : ''}"
  >
    <p class="message-content">{message.content}</p>
    {#if message.role === 'assistant' && message.query_time}
      <p class="meta-text query-time">Time: {message.query_time.toFixed(2)}s</p>
    {/if}
    {#if message.role === 'assistant' && message.prompt_token_count}
      <p class="meta-text token-count">Tokens: {message.prompt_token_count}</p>
    {/if}
    {#if message.isError}
      <p class="meta-text error-text">Error occurred</p>
    {/if}
  </div>
  {#if message.role === 'user'}
    <div class="avatar user-avatar">
      {userAvatar}
    </div>
  {/if}
</div>

<style>
  .chat-message-container {
    display: flex;
    align-items: flex-end;
    margin-bottom: 1rem; /* Replaces mb-4 */
  }

  .chat-message-container.user {
    justify-content: flex-end;
  }

  .chat-message-container.assistant {
    justify-content: flex-start;
  }

  .avatar {
    flex-shrink: 0;
    width: 36px; /* w-9 */
    height: 36px; /* h-9 */
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem; /* text-xl */
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); /* shadow-md */
  }

  .assistant-avatar {
    background: linear-gradient(to bottom right, #63b3ed, #2b6cb0); /* from-blue-400 to-blue-700 */
    margin-right: 0.75rem; /* mr-3 */
  }

  .user-avatar {
     background: linear-gradient(to bottom right, #a0aec0, #4a5568); /* from-gray-400 to-gray-700 */
     margin-left: 0.75rem; /* ml-3 */
  }

  .message-bubble {
    max-width: 672px; /* max-w-2xl */
    padding: 0.75rem 1.25rem; /* px-5 py-3 */
    border-radius: 1rem; /* rounded-2xl */
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); /* shadow-lg */
    position: relative;
    border: 1px solid transparent; /* Base border for consistency */
  }

  .message-bubble.user {
    background: linear-gradient(to bottom right, #4299e1, #2b6cb0); /* from-blue-500 to-blue-700 */
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 0.375rem; /* rounded-br-md */
  }

  .message-bubble.assistant {
    background-color: white;
    color: #2d3748; 
    margin-right: auto;
    border-bottom-left-radius: 0.375rem; /* rounded-bl-md */
    border: 1px solid #e2e8f0; /* border-gray-200 */
  }

  /* Consider adding dark mode styles here if needed, similar to +page.svelte */
  /* @media (prefers-color-scheme: dark) {
    .message-bubble.assistant {
       background-color: #2d3748; // dark:bg-gray-800
       color: #f7fafc; // dark:text-gray-100
       border-color: #4a5568; // dark:border-gray-700
    }
  } */

  .message-bubble.error {
     border-color: #e53e3e; /* border-red-500 */
  }

  .message-content {
    font-size: 1rem; /* text-base */
    white-space: pre-wrap;
    line-height: 1.6; /* leading-relaxed approximation */
  }

  .meta-text {
    font-size: 0.75rem; /* text-xs */
    margin-top: 0.25rem; /* mt-1 */
  }
  
  .query-time {
    text-align: right;
    color: #a0aec0; /* text-gray-400 */
  }

  .token-count {
    text-align: right;
    color: #a0aec0; /* text-gray-400 */
  }

  .error-text {
    color: #e53e3e; /* text-red-500 */
  }
</style> 