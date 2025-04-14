<script>
  // Props: message (object with role: 'user'|'assistant', content: string, isError?: boolean, query_time?: number)
  export let message;
</script>

<div 
  class="p-4 rounded-lg mb-4 max-w-xl shadow-md transition-all duration-200 ease-in-out 
    {message.role === 'user' 
      ? 'bg-primary dark:bg-primary-dark text-white ml-auto rounded-br-none' 
      : 'bg-white dark:bg-dark-surface text-gray-800 dark:text-dark-text mr-auto rounded-bl-none'} 
    {message.isError ? 'border-2 border-red-500 dark:border-red-400' : 'border border-transparent'}"
>
  <p class="text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>
  
  <div class="flex justify-end items-center mt-2 pt-1 border-t border-opacity-20 
      {message.role === 'user' ? 'border-white' : 'border-gray-300 dark:border-gray-600'}">
    {#if message.role === 'assistant' && message.query_time}
      <p class="text-xs 
          {message.role === 'user' ? 'text-blue-100 dark:text-blue-200' : 'text-gray-500 dark:text-dark-text-secondary'}"
      >
        Query time: {message.query_time.toFixed(2)}s
      </p>
    {/if}
    {#if message.isError}
      <p class="text-xs text-red-300 dark:text-red-400 ml-auto font-medium">Error processing message</p>
    {/if}
  </div>
</div> 