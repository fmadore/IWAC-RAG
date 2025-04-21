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

<div class="source-panel">
  <h3 class="panel-title">Sources{#if sources.length > 0} ({sources.length}){/if}</h3>
  {#if sources.length > 0}
    <ul class="source-list">
      {#each sources as source (source.id)}
        <li class="source-item">
          <h4 class="source-title">{source.title}</h4>
          {#if source.newspaper || source.date}
            <p class="source-meta">
              {#if source.newspaper}{source.newspaper}{/if}{#if source.newspaper && source.date}, {/if}{#if source.date}{source.date}{/if}
            </p>
          {/if}
          <p class="source-snippet">"${source.text_snippet}"</p>
          
          {#if source.url && source.url.trim() !== ''}
            <!-- Link to original URL if available -->
            <a href={source.url} target="_blank" rel="noopener noreferrer" class="source-link">
              View Original Source
            </a>
          {:else}
             <!-- Fallback to ZMO database link -->
             {@const displayId = source.id.replace('article_', '')}
             <a href={`https://islam.zmo.de/s/afrique_ouest/item/${displayId}`} target="_blank" rel="noopener noreferrer" class="source-link">
               View on Collection Islam Afrique de l'Ouest (ID: {displayId})
             </a>
          {/if}
        </li>
      {/each}
    </ul>
  {:else}
    <p class="no-sources-text">No sources found for the last query.</p>
  {/if}
</div>

<style>
  .source-panel {
    /* Styling handled by parent's .source-panel-container */
    display: flex;
    flex-direction: column;
  }

  .panel-title {
    /* Reuse styles from FilterPanel: text-xl font-semibold mb-4 border-b border-blue-100 pb-2 */
    font-size: 1.25rem; 
    font-weight: 600; 
    margin-bottom: 1rem; 
    padding-bottom: 0.5rem; 
    border-bottom: 1px solid #e2e8f0; /* Adjusted border color */
    color: #1a202c;
  }

  .source-list {
    /* Replaces space-y-4 */
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 1rem; /* space-y-4 */
  }

  .source-item {
    /* Replaces border border-blue-100 rounded-xl p-4 bg-gradient shadow-sm */
    border: 1px solid #bee3f8; /* Adjusted border color */
    border-radius: 0.75rem; /* rounded-xl */
    padding: 1rem; /* p-4 */
    background: linear-gradient(to bottom right, #f7fafc, #ebf8ff); /* from-gray-50 to-blue-50 */
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); /* shadow-sm */
    transition: box-shadow 0.2s ease;
  }
  
  .source-item:hover {
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  }

  .source-title {
    /* Replaces font-semibold text-base mb-1 text-blue-800 */
    font-weight: 600;
    font-size: 1rem; /* text-base */
    margin-bottom: 0.25rem; /* mb-1 */
    color: #2b6cb0; /* text-blue-800 */
  }

  .source-meta {
    /* Replaces text-xs text-gray-500 mb-1 */
    font-size: 0.75rem; /* text-xs */
    color: #718096; /* text-gray-500 */
    margin-bottom: 0.25rem; /* mb-1 */
  }

  .source-snippet {
    /* Replaces text-sm italic text-gray-700 mb-2 */
    font-size: 0.875rem; /* text-sm */
    font-style: italic;
    color: #4a5568; /* text-gray-700 */
    margin-bottom: 0.5rem; /* mb-2 */
    /* Add some line clamping if snippets can be long */
    /* display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;  
    overflow: hidden; */
  }

  .source-link {
    /* Replaces text-xs text-blue-600 hover:underline font-medium */
    font-size: 0.75rem; /* text-xs */
    color: #3182ce; /* text-blue-600 */
    text-decoration: none;
    font-weight: 500; /* font-medium */
  }

  .source-link:hover {
    text-decoration: underline;
  }
  
  .no-sources-text {
    /* Replaces text-sm text-gray-400 */
    font-size: 0.875rem; /* text-sm */
    color: #a0aec0; /* text-gray-400 */
    text-align: center;
    padding: 1rem 0;
  }
  
  /* Optional Dark Mode Styles */
  /* 
  @media (prefers-color-scheme: dark) {
     .panel-title { color: #e2e8f0; border-bottom-color: #4a5568; } 
     .source-item { 
        border-color: #4a5568; // dark:border-gray-700
        background: linear-gradient(to bottom right, #2d3748, #1a202c); // dark:from-gray-900 dark:to-gray-800 approximation
     } 
     .source-title { color: #63b3ed; } // dark:text-blue-300
     .source-meta { color: #a0aec0; } // dark:text-gray-400
     .source-snippet { color: #cbd5e0; } // dark:text-gray-300
     .source-link { color: #63b3ed; } // dark:text-blue-400
     .no-sources-text { color: #718096; } // dark:text-gray-500
  } 
  */
</style> 