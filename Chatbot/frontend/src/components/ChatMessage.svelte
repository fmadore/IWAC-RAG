<script>
  // Props: message (object with role: 'user'|'assistant', content: string, isError?: boolean, query_time?: number)
  export let message;
</script>

<div class="p-3 rounded-lg mb-2 {message.role === 'user' ? 'bg-blue-100 dark:bg-blue-900 ml-auto' : 'bg-gray-200 dark:bg-gray-700 mr-auto'} max-w-xl {message.isError ? 'border border-red-500' : ''}">
  <p class="text-sm whitespace-pre-wrap">{message.content}</p>
  {#if message.role === 'assistant' && message.query_time}
    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 text-right">Time: {message.query_time.toFixed(2)}s</p>
  {/if}
  {#if message.isError}
     <p class="text-xs text-red-500 mt-1">Error occurred</p>
  {/if}
</div> 