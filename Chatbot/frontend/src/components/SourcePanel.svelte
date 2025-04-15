<script context="module" lang="ts">
  export interface Source {
    id: string;
    title: string;
    newspaper?: string;
    date?: string;
    text_snippet: string;
    url?: string;
  }
</script>

<script lang="ts">
  // Props: sources (array of source objects from API: {id, title, newspaper, date, text_snippet, url?})
  export let sources: Source[] = [];
</script>

<div class="p-4 bg-white/90 dark:bg-gray-900/90 rounded-2xl shadow-lg border border-blue-100 dark:border-gray-800">
  <h3 class="text-xl font-semibold mb-4 border-b border-blue-100 dark:border-gray-700 pb-2">Sources</h3>
  {#if sources.length > 0}
    <ul class="space-y-4">
      {#each sources as source (source.id)}
        <li class="border border-blue-100 dark:border-gray-700 rounded-xl p-4 bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 shadow-sm">
          <h4 class="font-semibold text-base mb-1 text-blue-800 dark:text-blue-300">{source.title}</h4>
          {#if source.newspaper || source.date}
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">
              {#if source.newspaper}{source.newspaper}{/if}{#if source.newspaper && source.date}, {/if}{#if source.date}{source.date}{/if}
            </p>
          {/if}
          <p class="text-sm italic text-gray-700 dark:text-gray-300 mb-2">"{source.text_snippet}"</p>
          {#if source.url}
            <a href={source.url} target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium">
              View Original (ID: {source.id})
            </a>
          {:else}
             <p class="text-xs text-gray-400 dark:text-gray-500">(ID: {source.id})</p>
          {/if}
        </li>
      {/each}
    </ul>
  {:else}
    <p class="text-sm text-gray-400 dark:text-gray-500">No sources found for the last query.</p>
  {/if}
</div> 