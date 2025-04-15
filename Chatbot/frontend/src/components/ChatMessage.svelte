<script>
  // Props: message (object with role: 'user'|'assistant', content: string, isError?: boolean, query_time?: number)
  export let message;
  // Avatars (could be replaced with real images)
  const userAvatar = '🧑';
  const assistantAvatar = '🤖';
</script>

<div class="flex items-end mb-4 {message.role === 'user' ? 'justify-end' : 'justify-start'}">
  {#if message.role === 'assistant'}
    <div class="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-blue-700 flex items-center justify-center text-xl shadow-md mr-3">
      {assistantAvatar}
    </div>
  {/if}
  <div class="max-w-2xl px-5 py-3 rounded-2xl shadow-lg relative 
    {message.role === 'user' 
      ? 'bg-gradient-to-br from-blue-500 to-blue-700 text-white ml-auto rounded-br-md' 
      : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 mr-auto rounded-bl-md border border-gray-200 dark:border-gray-700'}
    {message.isError ? 'border border-red-500' : ''}">
    <p class="text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>
    {#if message.role === 'assistant' && message.query_time}
      <p class="text-xs text-right mt-1 text-gray-400">Time: {message.query_time.toFixed(2)}s</p>
    {/if}
    {#if message.isError}
      <p class="text-xs text-red-500 mt-1">Error occurred</p>
    {/if}
  </div>
  {#if message.role === 'user'}
    <div class="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-gray-400 to-gray-700 flex items-center justify-center text-xl shadow-md ml-3">
      {userAvatar}
    </div>
  {/if}
</div> 