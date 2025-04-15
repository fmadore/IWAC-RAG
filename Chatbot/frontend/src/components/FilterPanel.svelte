<script context="module" lang="ts">
  export interface DateRange {
    from?: string;
    to?: string;
    min?: string;
    max?: string;
  }

  export interface FilterOptions {
    newspapers: string[];
    locations: string[];
    subjects: string[];
    date_range: { min?: string; max?: string };
  }

  export interface Filters {
    date_range?: { from?: string; to?: string };
    newspaper?: string;
    locations?: string[];
    subjects?: string[];
  }
</script>

<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let options: FilterOptions;
  export let currentFilters: Filters = {};
  export let selectedModel: string = 'gemma3:4b';

  const dispatch = createEventDispatcher();

  // Local state for inputs
  let dateFrom = currentFilters.date_range?.from || '';
  let dateTo = currentFilters.date_range?.to || '';
  let selectedNewspaper = currentFilters.newspaper || '';
  let selectedLocations = currentFilters.locations || [];
  let selectedSubjects = currentFilters.subjects || [];

  // Available models (can be fetched or configured later)
  const availableModels = [
    { id: 'gemma3:4b', name: 'Ollama: Gemma3 4B' },
    { id: 'deepseek-r1:7b', name: 'Ollama: Deepseek R1 7B' },
    { id: 'gemini-2.0-flash', name: 'Gemini: 2.0 Flash' },
    { id: 'gemini-pro', name: 'Gemini: Pro' },
    // Add more models here as needed
  ];

  function applyFilters() {
    const newFilters: Filters = {};
    if (dateFrom || dateTo) {
      newFilters.date_range = {};
      if (dateFrom) newFilters.date_range.from = dateFrom;
      if (dateTo) newFilters.date_range.to = dateTo;
    }
    if (selectedNewspaper) {
      newFilters.newspaper = selectedNewspaper;
    }
    if (selectedLocations.length > 0) {
      newFilters.locations = selectedLocations;
    }
     if (selectedSubjects.length > 0) {
      newFilters.subjects = selectedSubjects;
    }
    
    // Update the parent's filter state
    currentFilters = newFilters; 
    dispatch('update', newFilters);
  }

  function resetFilters() {
    dateFrom = '';
    dateTo = '';
    selectedNewspaper = '';
    selectedLocations = [];
    selectedSubjects = [];
    currentFilters = {};
    dispatch('reset');
    // Need to also trigger an update event if parent relies on it
    dispatch('update', {}); 
  }

  // Reactive statement to update local state if parent changes filters externally
  $: {
      dateFrom = currentFilters.date_range?.from || '';
      dateTo = currentFilters.date_range?.to || '';
      selectedNewspaper = currentFilters.newspaper || '';
      selectedLocations = currentFilters.locations || [];
      selectedSubjects = currentFilters.subjects || [];
  }

  // Reactive statement to dispatch model change event when selection changes
  $: {
    if (selectedModel) { // Ensure it has a value
      dispatch('modelchange', { model: selectedModel });
    }
  }
</script>

<div class="filter-panel">
  <h3 class="panel-title">Filters</h3>

  <!-- Model Selection -->
  <div class="form-section">
    <label for="model-select" class="input-label">Language Model</label>
    <select id="model-select" bind:value={selectedModel} class="select-input">
      {#each availableModels as model}
        <option value={model.id}>{model.name}</option>
      {/each}
    </select>
  </div>

  <!-- Date Range -->
  <div class="form-section">
    <label class="input-label">Date Range</label>
    <div class="date-input-group">
      <input type="date" bind:value={dateFrom} class="date-input" placeholder="From" aria-label="Date from">
      <input type="date" bind:value={dateTo} class="date-input" placeholder="To" aria-label="Date to">
    </div>
     {#if options.date_range && (options.date_range.min || options.date_range.max)}
       <p class="info-text">
         Available: {options.date_range.min || 'N/A'} to {options.date_range.max || 'N/A'}
        </p>
     {/if}
  </div>

  <!-- Newspaper -->
  <div class="form-section">
    <label for="newspaper-select" class="input-label">Newspaper</label>
    <select id="newspaper-select" bind:value={selectedNewspaper} class="select-input">
      <option value="">All Newspapers</option>
      {#if options.newspapers}
        {#each options.newspapers as newspaper}
          <option value={newspaper}>{newspaper}</option>
        {/each}
      {/if}
    </select>
  </div>

  <!-- Locations -->
  <div class="form-section">
     <label for="locations-select" class="input-label">Locations</label>
     {#if options.locations && options.locations.length > 0}
       <select id="locations-select" multiple bind:value={selectedLocations} class="multi-select-input">
         {#each options.locations as location}
           <option value={location}>{location}</option>
         {/each}
       </select>
       <p class="info-text small-text">Hold Ctrl/Cmd to select multiple.</p>
     {:else}
        <p class="no-options-text">No location filters available.</p>
     {/if}
   </div>

   <!-- Subjects -->
  <div class="form-section">
     <label for="subjects-select" class="input-label">Subjects</label>
     {#if options.subjects && options.subjects.length > 0}
       <select id="subjects-select" multiple bind:value={selectedSubjects} class="multi-select-input">
         {#each options.subjects as subject}
           <option value={subject}>{subject}</option>
         {/each}
       </select>
       <p class="info-text small-text">Hold Ctrl/Cmd to select multiple.</p>
     {:else}
        <p class="no-options-text">No subject filters available.</p>
     {/if}
   </div>

  <!-- Buttons -->
  <div class="button-container">
    <button on:click={resetFilters} class="reset-button">Reset</button>
    <button on:click={applyFilters} class="apply-button">Apply</button>
  </div>
</div>

<style>
  .filter-panel {
    /* Replaces p-4, bg-white/90, rounded-2xl, shadow-lg, border, border-blue-100 */
    /* Background/border etc handled by parent's .filter-sidebar now, only need internal layout */
    display: flex;
    flex-direction: column;
    gap: 1.5rem; /* space-y-6 approximation */
  }

  .panel-title {
    /* Replaces text-xl font-semibold mb-4 border-b border-blue-100 pb-2 */
    font-size: 1.25rem; 
    font-weight: 600; 
    margin-bottom: 1rem; 
    padding-bottom: 0.5rem; 
    border-bottom: 1px solid #e2e8f0; /* Adjusted border color */
    color: #1a202c;
  }

  .form-section {
    /* Container for label + input group */
  }

  .input-label {
    /* Replaces block text-sm font-medium mb-1 */
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.25rem;
    color: #4a5568; /* Darker gray for labels */
  }

  /* Common Input Styles */
  .select-input,
  .date-input,
  .multi-select-input {
    /* Replaces w-full p-2 border border-blue-100 rounded-lg text-sm */
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #cbd5e0; /* Adjusted border color */
    border-radius: 0.5rem; /* rounded-lg */
    font-size: 0.875rem; /* text-sm */
    background-color: #f7fafc; /* Lighter background */
    color: #2d3748;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .select-input:focus,
  .date-input:focus,
  .multi-select-input:focus {
     /* Replaces focus:ring-2 focus:ring-blue-400 */
    outline: none;
    border-color: #4299e1;
    box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.5);
  }

  /* Specific Input Styles */
  .date-input-group {
     /* Replaces flex gap-2 */
    display: flex;
    gap: 0.5rem;
  }

  .multi-select-input {
     /* Replaces h-28 */
    height: 7rem; 
  }

  .info-text {
     /* Replaces text-xs text-gray-500 mt-1 */
    font-size: 0.75rem;
    color: #718096;
    margin-top: 0.25rem;
  }
  
  .small-text {
      font-size: 0.7rem; /* Even smaller for the ctrl/cmd hint */
  }

  .no-options-text {
     /* Replaces text-sm text-gray-500 */
    font-size: 0.875rem;
    color: #718096;
  }

  .button-container {
     /* Replaces flex justify-between pt-4 border-t border-blue-100 mt-2 */
    display: flex;
    justify-content: space-between;
    padding-top: 1rem;
    border-top: 1px solid #e2e8f0; /* Adjusted border color */
    margin-top: 0.5rem;
  }

  /* Common Button Styles */
  .reset-button,
  .apply-button {
    /* Replaces px-4 py-1.5 text-sm rounded-lg transition-colors font-medium/semibold */
    padding: 0.375rem 1rem; /* py-1.5 px-4 */
    font-size: 0.875rem; /* text-sm */
    border-radius: 0.5rem; /* rounded-lg */
    cursor: pointer;
    transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    border: 1px solid transparent;
  }

  .reset-button {
    /* Replaces border border-blue-200 text-blue-700 hover:bg-blue-50 font-medium */
    border-color: #bee3f8; /* border-blue-200 */
    color: #2b6cb0; /* text-blue-700 */
    background-color: transparent;
    font-weight: 500;
  }

  .reset-button:hover {
    background-color: #ebf8ff; /* hover:bg-blue-50 */
    border-color: #90cdf4;
  }

  .apply-button {
    /* Replaces bg-blue-600 text-white hover:bg-blue-700 font-semibold shadow */
    background-color: #4299e1; /* bg-blue-600 */
    color: white;
    font-weight: 600; /* font-semibold */
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); /* shadow */
  }

  .apply-button:hover {
    background-color: #2b6cb0; /* hover:bg-blue-700 */
  }

  /* Optional Dark Mode Styles */
  /* 
  @media (prefers-color-scheme: dark) {
     .filter-panel { ... } 
     .panel-title { color: #e2e8f0; border-bottom-color: #4a5568; } 
     .input-label { color: #a0aec0; } 
     .select-input, .date-input, .multi-select-input { 
        background-color: #2d3748; // dark:bg-gray-800
        border-color: #4a5568; // dark:border-gray-700
        color: #e2e8f0;
     } 
     .info-text, .no-options-text { color: #718096; } // dark:text-gray-400 / 500
     .button-container { border-top-color: #4a5568; } 
     .reset-button { 
        border-color: #4a5568; // dark:border-gray-700
        color: #63b3ed; // dark:text-blue-300
     } 
     .reset-button:hover { 
        background-color: #2d3748; // dark:hover:bg-gray-800
     } 
     // Apply button is likely fine as is, but could adjust hover 
  } 
  */
</style> 