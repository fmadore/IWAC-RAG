<script>
  import { onMount } from 'svelte';
  import ChatMessage from '../components/ChatMessage.svelte';
  import FilterPanel from '../components/FilterPanel.svelte';
  import SourcePanel from '../components/SourcePanel.svelte';
  
  // State
  let query = '';
  let messages = [];
  let sources = [];
  let activeFilters = {};
  let isLoading = false;
  let selectedModel = 'gemma3:4b'; // Default model
  let filterOptions = {
    newspapers: [],
    locations: [],
    subjects: [],
    date_range: { min: null, max: null }
  };
  let showFilters = false;
  
  // Read API URL from environment variable (set during build or runtime)
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'; 
  console.log(`API URL: ${API_URL}`); // Log API URL for debugging

  // Load filter options on mount
  onMount(async () => {
    try {
      console.log("Fetching filters from:", `${API_URL}/filters`);
      const response = await fetch(`${API_URL}/filters`);
      if (response.ok) {
        filterOptions = await response.json();
        console.log("Filter options loaded:", filterOptions);
      } else {
        console.error('Failed to load filters:', response.status, response.statusText);
        // Add user-facing error message if desired
        messages = [...messages, { role: 'assistant', content: `Error loading filter options: ${response.statusText}`, isError: true }];
      }
    } catch (error) {
      console.error('Error loading filters:', error);
      messages = [...messages, { role: 'assistant', content: `Network error loading filter options: ${error}. Is the backend running?`, isError: true }];
      // Add user-facing error message if desired
    }
  });
  
  // Submit query
  async function submitQuery() {
    if (!query.trim()) return;
    
    // Add user message
    messages = [...messages, { 
      role: 'user', 
      content: query 
    }];
    
    // Clear sources from previous query
    sources = [];
    
    // Show loading state
    isLoading = true;
    const userQuery = query;
    query = ''; // Clear input immediately
    
    try {
      console.log("Submitting query to:", `${API_URL}/query`);
      console.log("Query data:", JSON.stringify({
          query: userQuery,
          filters: Object.keys(activeFilters).length > 0 ? activeFilters : null, 
          top_k: 5,
          model_name: selectedModel
        }));

      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          // Send null if no filters are active, matching API expectation
          filters: Object.keys(activeFilters).length > 0 ? activeFilters : null, 
          top_k: 5,
          model_name: selectedModel
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log("Query response received:", result);
        
        // Add assistant message
        messages = [...messages, {
          role: 'assistant',
          content: result.answer,
          query_time: result.query_time
        }];
        
        // Update sources
        sources = result.sources;
      } else {
        const errorText = await response.text(); // Get raw error text
        console.error('Error submitting query:', response.status, response.statusText, errorText);
        let detail = response.statusText;
        try { 
          const errorData = JSON.parse(errorText);
          detail = errorData.detail || detail;
        } catch(e) { /* Ignore if error response is not JSON */ }

        // Add error message
        messages = [...messages, {
          role: 'assistant',
          content: `Sorry, there was an error (${response.status}): ${detail}. Please check the backend logs.`,
          isError: true
        }];
      }
    } catch (error) {
      console.error('Network or other error submitting query:', error);
      messages = [...messages, {
        role: 'assistant',
        content: `Sorry, there was a network error connecting to the server: ${error}. Is the backend running and accessible at ${API_URL}?`,
        isError: true
      }];
    } finally {
      isLoading = false;
    }
  }
  
  // Handle filter changes (triggered by FilterPanel component)
  function handleFilterUpdate(event) {
    activeFilters = event.detail;
    console.log("Filters updated:", activeFilters);
    // Optionally re-submit query when filters change?
    // submitQuery(); // If desired
  }
  
  // Reset filters (triggered by FilterPanel component)
  function handleFilterReset() {
    activeFilters = {};
    console.log("Filters reset");
     // Optionally re-submit query when filters reset?
    // submitQuery(); // If desired
  }
  
  // Handle model selection change
  function handleModelChange(event) {
    selectedModel = event.detail.model;
    console.log("Model selected:", selectedModel);
    // Potentially trigger a re-query or inform the user?
  }
</script>

<!-- Basic HTML Structure -->
<!-- Assumes TailwindCSS or similar utility classes are set up -->
<main class="flex flex-col h-screen max-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  <header class="bg-blue-700 text-white p-4 shadow-md flex-shrink-0">
    <div class="container mx-auto flex justify-between items-center">
      <h1 class="text-xl font-bold">Islam West Africa Collection (IWAC) ChatBot</h1>
      <button 
        on:click={() => showFilters = !showFilters}
        class="px-3 py-1 bg-blue-600 hover:bg-blue-800 rounded flex items-center transition-colors"
        aria-label="Toggle Filters"
        aria-expanded={showFilters}
      >
        <!-- Using a simple text icon for now -->
        <span class="mr-1">☰</span> 
        Filters
      </button>
    </div>
  </header>
  
  <div class="flex flex-1 overflow-hidden">
    <!-- Filter sidebar -->
    {#if showFilters}
      <aside class="w-64 bg-white dark:bg-gray-800 shadow-md p-4 overflow-y-auto flex-shrink-0 border-r dark:border-gray-700">
        <FilterPanel 
          options={filterOptions} 
          currentFilters={activeFilters} 
          selectedModel={selectedModel}
          on:update={handleFilterUpdate} 
          on:reset={handleFilterReset} 
          on:modelchange={handleModelChange}
        />
      </aside>
    {/if}
    
    <!-- Main content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Chat messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" aria-live="polite">
        {#each messages as message, i (message.role + i)} <!-- Basic keying -->
          <ChatMessage {message} />
        {:else}
          <!-- Welcome Message -->
          <div class="h-full flex items-center justify-center text-center text-gray-500 dark:text-gray-400">
            <div>
              <h2 class="text-2xl font-semibold mb-3">Welcome to the IWAC ChatBot</h2>
              <p class="max-w-md mx-auto">
                Ask questions about Islam and Muslims in West Africa based on our collection
                of newspaper articles.
              </p>
              <p class="mt-4 text-sm">Use the input below to start chatting, or open the filters panel to refine your search.</p>
            </div>
          </div>
        {/each}
        
        <!-- Loading Indicator -->
        {#if isLoading}
          <div class="flex justify-center p-4">
            <div class="loader" aria-label="Loading response"></div>
          </div>
        {/if}
      </div>
      
      <!-- Input area -->
      <div class="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800 flex-shrink-0">
        <form on:submit|preventDefault={submitQuery} class="flex gap-2">
          <input 
            type="text" 
            bind:value={query} 
            placeholder="Ask a question..." 
            class="flex-1 p-2 border border-gray-300 rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
            aria-label="Chat input"
          />
          <button 
            type="submit" 
            class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
            disabled={isLoading || !query.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
    
    <!-- Sources panel -->
    {#if sources.length > 0}
      <aside class="w-80 bg-white dark:bg-gray-800 shadow-md p-4 overflow-y-auto flex-shrink-0 border-l dark:border-gray-700">
        <SourcePanel {sources} />
      </aside>
    {/if}
  </div>
</main>

<style>
  /* Basic CSS for loader - assumes no external CSS library is fully set up */
  .loader {
    border: 4px solid #f3f3f3; /* Light grey */
    border-top: 4px solid #3498db; /* Blue */
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Ensure main layout uses full height */
  main {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }

  /* Allow content area to scroll */
  .flex-1.overflow-y-auto {
    flex-grow: 1;
  }
</style>
