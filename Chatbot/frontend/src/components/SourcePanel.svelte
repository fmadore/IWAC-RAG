<script>
  // Props: sources (array of source objects from API: {id, title, newspaper, date, text_snippet, url?})
  export let sources = [];
</script>

<div class="p-1 text-sm">
  <h3 class="text-xl font-semibold mb-5 border-b border-gray-200 dark:border-gray-600 pb-3 text-gray-900 dark:text-dark-text">Sources</h3>
  {#if sources.length > 0}
    <ul class="space-y-4">
      {#each sources as source (source.id)}
        <li class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800 shadow-sm transition-colors hover:bg-gray-50 dark:hover:bg-gray-750">
          <h4 class="font-semibold text-base mb-1.5 text-gray-800 dark:text-dark-text">{source.title || 'Untitled Article'}</h4>
          {#if source.newspaper || source.date}
            <p class="text-xs text-gray-500 dark:text-dark-text-secondary mb-2">
              {#if source.newspaper}<span class="font-medium">{source.newspaper}</span>{/if}{#if source.newspaper && source.date}, {/if}{#if source.date}{source.date}{/if}
            </p>
          {/if}
          <blockquote class="text-sm text-gray-600 dark:text-gray-300 mb-3 border-l-4 border-primary-light dark:border-primary-dark pl-3 italic">
             "{source.text_snippet}"
          </blockquote>
          
          <div class="flex justify-between items-center text-xs">
             <p class="text-gray-400 dark:text-gray-500">ID: {source.id}</p>
             {#if source.url}
               <a 
                 href={source.url} 
                 target="_blank" 
                 rel="noopener noreferrer" 
                 class="text-primary dark:text-primary-light hover:underline font-medium flex items-center"
               >
                 View Original
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                   <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                 </svg>
               </a>
             {/if}
          </div>
        </li>
      {/each}
    </ul>
  {:else}
    <div class="text-center py-8 px-4 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg mt-4">
      <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-10 w-10 text-gray-400 dark:text-gray-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
      </svg>
      <p class="text-sm text-gray-500 dark:text-dark-text-secondary">No sources cited for the last response.</p>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Sources will appear here when available.</p>
    </div>
  {/if}
</div> 