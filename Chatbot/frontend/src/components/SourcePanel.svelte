<script>
  // Props: sources (array of source objects from API: {id, title, newspaper, date, text_snippet, url?})
  export let sources = [];
</script>

<div class="p-2">
  <h3 class="text-lg font-semibold mb-3 border-b pb-2 dark:border-gray-600">Sources</h3>
  {#if sources.length > 0}
    <ul class="space-y-3">
      {#each sources as source (source.id)}
        <li class="border rounded dark:border-gray-700 p-3 bg-gray-50 dark:bg-gray-850">
          <h4 class="font-medium text-sm mb-1">{source.title}</h4>
          {#if source.newspaper || source.date}
            <p class="text-xs text-gray-600 dark:text-gray-400 mb-1">
              {#if source.newspaper}{source.newspaper}{/if}{#if source.newspaper && source.date}, {/if}{#if source.date}{source.date}{/if}
            </p>
          {/if}
          <p class="text-sm italic text-gray-700 dark:text-gray-300 mb-2">"{source.text_snippet}"</p>
          {#if source.url}
            <a href={source.url} target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">
              View Original (ID: {source.id})
            </a>
          {:else}
             <p class="text-xs text-gray-500 dark:text-gray-400">(ID: {source.id})</p>
          {/if}
        </li>
      {/each}
    </ul>
  {:else}
    <p class="text-sm text-gray-500 dark:text-gray-400">No sources found for the last query.</p>
  {/if}
</div> 