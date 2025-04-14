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
<main class="flex flex-col h-screen max-h-screen bg-secondary-light dark:bg-dark-bg text-gray-900 dark:text-dark-text font-sans">
  <header class="bg-primary dark:bg-primary-dark text-white p-4 shadow-lg flex-shrink-0 z-10">
    <div class="container mx-auto flex justify-between items-center">
      <h1 class="text-2xl font-semibold tracking-tight">IWAC ChatBot</h1>
      <button 
        on:click={() => showFilters = !showFilters}
        class="px-4 py-2 bg-primary-dark dark:bg-primary text-white rounded-md hover:bg-opacity-90 dark:hover:bg-opacity-90 flex items-center transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-dark"
        aria-label="Toggle Filters"
        aria-expanded={showFilters}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h7" />
        </svg>
        Filters
      </button>
    </div>
  </header>
  
  <div class="flex flex-1 overflow-hidden">
    <!-- Filter sidebar -->
    {#if showFilters}
      <aside class="w-72 bg-white dark:bg-dark-surface shadow-lg p-5 overflow-y-auto flex-shrink-0 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out">
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
    <div class="flex-1 flex flex-col overflow-hidden min-w-0 bg-secondary-light dark:bg-dark-bg">
      <!-- Chat messages -->
      <div class="flex-1 overflow-y-auto p-6 space-y-5" aria-live="polite">
        {#each messages as message, i (message.role + i)} <!-- Basic keying -->
          <ChatMessage {message} />
        {:else}
          <!-- Enhanced Welcome Message -->
          <div class="h-full flex flex-col items-center justify-center text-center text-gray-500 dark:text-dark-text-secondary p-8">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mb-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
               <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
             </svg>
              <h2 class="text-3xl font-semibold mb-4 text-gray-800 dark:text-dark-text">Welcome to the IWAC ChatBot</h2>
              <p class="max-w-lg mx-auto text-base mb-6">
                Explore insights on Islam and Muslims in West Africa through our digitized newspaper collection.
              </p>
              <p class="text-sm">
                Start by typing your question below, or use the <button class="text-primary hover:underline font-medium" on:click={() => showFilters = !showFilters}>Filters</button> panel to narrow your search.
              </p>
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
      <div class="border-t border-gray-200 dark:border-gray-600 p-4 bg-white dark:bg-dark-surface flex-shrink-0 shadow-up">
        <form on:submit|preventDefault={submitQuery} class="flex items-center gap-3 max-w-4xl mx-auto">
          <input 
            type="text" 
            bind:value={query} 
            placeholder="Ask about the collection..." 
            class="flex-1 form-input px-4 py-3 border border-gray-300 rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:text-dark-text focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent shadow-sm transition-all"
            disabled={isLoading}
            aria-label="Chat input"
          />
          <button 
            type="submit" 
            class="px-6 py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-dark-surface disabled:opacity-60 disabled:cursor-not-allowed transition-colors duration-200 shadow-sm flex items-center justify-center"
            disabled={isLoading || !query.trim()}
          >
             <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 {isLoading ? 'hidden' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
               <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
             </svg>
             {isLoading ? 'Thinking...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
    
    <!-- Sources panel -->
    {#if sources.length > 0}
       <aside class="w-80 bg-white dark:bg-dark-surface shadow-lg p-5 overflow-y-auto flex-shrink-0 border-l border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out">
        <SourcePanel {sources} />
      </aside>
    {/if}
  </div>
</main>

<style>
  /* Fallback for font */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

  /* Update loader to use primary color */
  .loader {
    border: 4px solid rgba(var(--color-primary-DEFAULT), 0.2); /* Use primary color with alpha */
    border-top-color: rgb(var(--color-primary-DEFAULT)); /* Use solid primary color */
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Ensure main layout uses full height and applies font */
  main {
    display: flex;
    flex-direction: column;
    height: 100vh;
    font-family: 'Inter', sans-serif; /* Example font - ensure it's loaded */
    scroll-behavior: smooth;
  }

  /* Custom shadow for input area */
  .shadow-up {
     box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1), 0 -2px 4px -2px rgba(0, 0, 0, 0.1);
  }

  /* Add smooth scrolling */
  .overflow-y-auto {
    scroll-behavior: smooth;
  }
</style>
