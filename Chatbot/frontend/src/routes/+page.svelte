<script lang="ts">
  import { onMount } from 'svelte';
  import ChatMessage from '../components/ChatMessage.svelte';
  import FilterPanel from '../components/FilterPanel.svelte';
  import SourcePanel from '../components/SourcePanel.svelte';
  import { saveConversationAsHtml } from '../lib/saveConversation'; // Import the save function
  
  // Types
  interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    isError?: boolean;
    query_time?: number;
    prompt_token_count?: number;
    answer_token_count?: number;
  }

  interface Source {
    id: string;
    title: string;
    newspaper?: string;
    date?: string;
    text_snippet: string;
    url?: string;
  }

  interface Filters {
    date_range?: { from?: string; to?: string };
    newspaper?: string;
    locations?: string[];
    subjects?: string[];
  }

  interface FilterOptions {
    newspapers: string[];
    locations: string[];
    subjects: string[];
    date_range: { min?: string; max?: string };
  }

  // State
  let query = '';
  let messages: ChatMessage[] = [];
  let sources: Source[] = [];
  let activeFilters: Filters = {};
  let isLoading = false;
  let selectedModel: string = 'gemma3:4b'; // Default model
  let filterOptions: FilterOptions = {
    newspapers: [],
    locations: [],
    subjects: [],
    date_range: { min: '', max: '' }
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
          model_name: selectedModel
        }));

      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          // Send null if no filters are active, matching API expectation
          filters: Object.keys(activeFilters).length > 0 ? activeFilters : null, 
          model_name: selectedModel
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log("Query response received:", result);
        
        // Add assistant message with token count
        messages = [...messages, {
          role: 'assistant',
          content: result.answer,
          query_time: result.query_time,
          prompt_token_count: result.prompt_token_count,
          answer_token_count: result.answer_token_count
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
  function handleFilterUpdate(event: CustomEvent<Filters>) {
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
  function handleModelChange(event: CustomEvent<{ model: string }>) {
    selectedModel = event.detail.model;
    console.log("Model selected:", selectedModel);
    // Potentially trigger a re-query or inform the user?
  }
</script>

<!-- Basic HTML Structure -->
<main class="app-container">
  <header class="app-header">
    <div class="header-content">
      <h1 class="app-title">
        <span class="title-icon">🤖</span> Islam West Africa Collection (IWAC) ChatBot
      </h1>
      <div class="header-buttons">
        <button 
          on:click={() => saveConversationAsHtml(messages, sources)}
          class="header-action-button save-button"
          aria-label="Save Conversation"
          title="Save Conversation as HTML"
          disabled={messages.length === 0}
        >
          <span class="button-icon">💾</span> Save
        </button>
        <button 
          on:click={() => showFilters = !showFilters}
          class="header-action-button filter-toggle-button"
          aria-label="Toggle Filters"
          title="Toggle Filters Panel"
          aria-expanded={showFilters}
        >
          <span class="button-icon">☰</span> Filters
        </button>
      </div>
    </div>
  </header>
  
  <div class="main-layout">
    <!-- Filter sidebar -->
    {#if showFilters}
      <aside class="filter-sidebar">
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
    <div class="main-content-area">
      <!-- Chat messages -->
      <div class="chat-messages-area" aria-live="polite">
        {#each messages as message, i (message.role + i)} <!-- Basic keying -->
          <ChatMessage {message} />
        {:else}
          <!-- Welcome Message -->
          <div class="welcome-message-container">
            <div class="welcome-message">
              <h2 class="welcome-title">Welcome to the IWAC ChatBot</h2>
              <p class="welcome-text">
                Ask questions about Islam and Muslims in West Africa based on our collection
                of newspaper articles.
              </p>
              <p class="welcome-prompt">Use the input below to start chatting, or open the filters panel to refine your search.</p>
            </div>
          </div>
        {/each}
        
        <!-- Loading Indicator -->
        {#if isLoading}
          <div class="loading-indicator-container">
            <div class="loader" aria-label="Loading response"></div>
          </div>
        {/if}
      </div>
      
      <!-- Input area -->
      <div class="input-area-container">
        <form on:submit|preventDefault={submitQuery} class="message-input-form">
          <input 
            type="text" 
            bind:value={query} 
            placeholder="Ask a question..." 
            class="message-input"
            disabled={isLoading}
            aria-label="Chat input"
          />
          <button 
            type="submit" 
            class="send-button"
            disabled={isLoading || !query.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
    
    <!-- Sources panel -->
    {#if sources.length > 0}
      <aside class="source-panel-container">
        <SourcePanel {sources} />
      </aside>
    {/if}
  </div>
</main>

<style>
  /* Base App Layout */
  .app-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-height: 100vh;
    background: linear-gradient(135deg, #f0f4f8, #e0e8f0); /* Lighter gradient */
    color: #2d3748; /* Darker text */
  }

  .app-header {
    background-color: rgba(255, 255, 255, 0.85); /* Slightly transparent white */
    backdrop-filter: blur(8px);
    padding: 1rem; /* 16px */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    flex-shrink: 0;
    border-bottom: 1px solid #e2e8f0; /* Light border */
    z-index: 20; /* Ensure header is above content */
  }

  .header-content {
    max-width: 1280px; /* Container max-width */
    margin-left: auto;
    margin-right: auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .app-title {
    font-size: 1.5rem; /* 24px */
    font-weight: 700;
    letter-spacing: -0.025em;
    display: flex;
    align-items: center;
    gap: 0.5rem; /* 8px */
    color: #1a202c; /* Very dark text */
  }
  
  .title-icon {
    color: #4299e1; /* Blue */
  }

  .header-buttons {
    display: flex;
    align-items: center;
    gap: 0.75rem; /* 12px */
  }

  .header-action-button { /* Common style for header buttons */
    padding: 0.5rem 0.75rem; /* Smaller padding */
    color: white;
    border: none;
    border-radius: 0.5rem; /* 8px */
    display: flex;
    align-items: center;
    gap: 0.25rem; /* 4px */
    cursor: pointer;
    transition: background-color 0.2s ease, opacity 0.2s ease;
    font-weight: 500;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  
  .save-button {
    background-color: #38a169; /* Green */
  }
  
  .save-button:hover:not(:disabled) {
    background-color: #2f855a; /* Darker Green */
  }
  
  .save-button:disabled {
    background-color: #9ae6b4; /* Lighter green when disabled */
    cursor: not-allowed;
    opacity: 0.7;
  }

  .filter-toggle-button {
    background-color: #4299e1; /* Blue */
  }

  .filter-toggle-button:hover {
    background-color: #2b6cb0; /* Darker blue */
  }

  .button-icon { /* Icon style for both buttons */
      display: inline-block;
      /* Add size or other styling if needed */
  }

  /* Main Layout */
  .main-layout {
    display: flex;
    flex: 1 1 0%; /* Grow to fill space */
    overflow: hidden; /* Prevent layout overflow */
    position: relative; /* For positioning children if needed */
  }

  /* Filter Sidebar */
  .filter-sidebar {
    width: 288px; /* w-72 */
    background-color: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    padding: 1.5rem; /* p-6 */
    overflow-y: auto;
    flex-shrink: 0;
    border-right: 1px solid #e2e8f0;
    border-radius: 0 1.5rem 1.5rem 0; /* rounded-tr-3xl rounded-br-3xl */
    z-index: 10; /* Above main content */
  }

  /* Main Content Area */
  .main-content-area {
    flex: 1 1 0%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-width: 0; /* Prevent flex item blowout */
  }

  /* Chat Messages */
  .chat-messages-area {
    flex: 1 1 0%;
    overflow-y: auto;
    padding: 1.5rem 2rem; /* py-6 sm:px-8 */
    /* Add subtle background pattern or keep clean */
  }
  
  /* Improve spacing between messages (will be applied by ChatMessage margin) */
  .chat-messages-area > * + * {
     margin-top: 1rem; /* space-y-4 */
  }

  /* Welcome Message */
  .welcome-message-container {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #718096; /* gray-500 */
  }

  .welcome-message {
    max-width: 448px; /* max-w-md */
    margin: 0 auto;
  }

  .welcome-title {
    font-size: 1.875rem; /* text-3xl */
    font-weight: 600;
    margin-bottom: 0.75rem; /* mb-3 */
    color: #4a5568; /* Slightly darker gray */
  }

  .welcome-text {
    line-height: 1.6;
  }
  
  .welcome-prompt {
     margin-top: 1rem; /* mt-4 */
     font-size: 1rem; /* text-base */
  }

  /* Loading Indicator */
  .loading-indicator-container {
    display: flex;
    justify-content: center;
    padding: 1rem; /* p-4 */
  }

  .loader {
    border: 4px solid #e2e8f0; /* Light grey border */
    border-top: 4px solid #4299e1; /* Blue spinner */
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Input Area */
  .input-area-container {
    position: relative; /* z-10 was used, keep relative positioning */
    z-index: 15; /* Above chat, below header/sidebars */
    padding: 0 0.5rem 1rem 0.5rem; /* mx-2 mb-4 */
    /* Padding adjustments for larger screens if needed */
    @media (min-width: 640px) {
       padding-left: 2rem; /* sm:mx-8 */
       padding-right: 2rem;
    }
  }

  .message-input-form {
    display: flex;
    align-items: center;
    gap: 0.75rem; /* gap-3 */
    background-color: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(8px);
    border-radius: 1rem; /* rounded-2xl */
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); /* shadow-xl */
    padding: 0.75rem 1rem; /* px-4 py-3 */
    border: 1px solid #e2e8f0;
  }

  .message-input {
    flex: 1 1 0%;
    background-color: transparent;
    padding: 0.75rem; /* p-3 */
    border: none;
    outline: none;
    font-size: 1.125rem; /* text-lg */
    color: #1a202c;
  }
  
  .message-input::placeholder {
    color: #a0aec0; /* placeholder-gray-400 */
  }

  .message-input:disabled {
      cursor: not-allowed;
  }

  .send-button {
    padding: 0.6rem 1.25rem; /* px-5 py-2ish */
    background-color: #4299e1; /* bg-blue-600 */
    color: white;
    font-weight: 600; /* font-semibold */
    border-radius: 0.75rem; /* rounded-xl */
    border: none;
    cursor: pointer;
    transition: background-color 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }

  .send-button:hover {
    background-color: #2b6cb0; /* hover:bg-blue-700 */
  }

  .send-button:focus {
    outline: 2px solid transparent;
    outline-offset: 2px;
     box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5); /* focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 */
  }

  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Source Panel */
  .source-panel-container {
    width: 384px; /* w-96 */
    background-color: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    padding: 1.5rem; /* p-6 */
    overflow-y: auto;
    flex-shrink: 0;
    border-left: 1px solid #e2e8f0;
    border-radius: 1.5rem 0 0 1.5rem; /* rounded-tl-3xl rounded-bl-3xl */
    z-index: 10;
  }

  /* Dark Mode Styles (Optional - can be added later if needed) */
  /* 
  @media (prefers-color-scheme: dark) {
    .app-container { background: linear-gradient(135deg, #1a202c, #2d3748); color: #e2e8f0; }
    .app-header { background-color: rgba(26, 32, 44, 0.85); border-bottom-color: #4a5568; }
    .header-content { }
    .app-title { color: #f7fafc; }
    .title-icon { color: #63b3ed; } // Lighter blue 
    // ... etc for all elements ...
    .message-input { color: #f7fafc; }
    .message-input::placeholder { color: #718096; }
    .filter-sidebar, .source-panel-container { background-color: rgba(26, 32, 44, 0.9); border-color: #4a5568; }
    .message-input-form { background-color: rgba(26, 32, 44, 0.95); border-color: #4a5568; }

  } 
  */

  /* Ensure main layout uses full height (already in app-container) */
  
  /* Allow content area to scroll (already handled by chat-messages-area) */

</style>
