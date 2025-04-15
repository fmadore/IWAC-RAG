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
  import YearSlider from './YearSlider.svelte';

  export let options: FilterOptions;
  export let currentFilters: Filters = {};
  export let selectedModel: string = 'gemma3:4b';

  const dispatch = createEventDispatcher();

  // Local state for inputs
  let filterStartYear: number | undefined;
  let filterEndYear: number | undefined;
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

  // Helper function to get year from date string (YYYY-MM-DD)
  function getYearFromDate(dateString?: string): number | undefined {
    if (!dateString) return undefined;
    try {
      // Ensure valid date format before parsing
      if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) return undefined;
      const year = new Date(dateString + 'T00:00:00Z').getUTCFullYear(); // Use UTC to avoid timezone issues
      return isNaN(year) ? undefined : year;
    } catch (e) {
      return undefined;
    }
  }

  // Calculate min/max years for the slider from options
  let minSliderYear: number | undefined;
  let maxSliderYear: number | undefined;
  $: {
    minSliderYear = getYearFromDate(options.date_range?.min);
    maxSliderYear = getYearFromDate(options.date_range?.max);
    // Initialize filter years if they are undefined and slider bounds are known
    if (filterStartYear === undefined && minSliderYear !== undefined) {
        filterStartYear = minSliderYear;
    }
    if (filterEndYear === undefined && maxSliderYear !== undefined) {
        filterEndYear = maxSliderYear;
    }
  }

  // Initialize filter years based on currentFilters
  $: {
      const initialStartYear = getYearFromDate(currentFilters.date_range?.from);
      const initialEndYear = getYearFromDate(currentFilters.date_range?.to);

      // Only update if currentFilters change *and* local state hasn't been set by user interaction yet
      // Or if the filter is reset externally
      if (currentFilters.date_range) {
          if (initialStartYear !== undefined) filterStartYear = initialStartYear;
          if (initialEndYear !== undefined) filterEndYear = initialEndYear;
      } else { // Handle external reset
         if (minSliderYear !== undefined) filterStartYear = minSliderYear; 
         if (maxSliderYear !== undefined) filterEndYear = maxSliderYear; 
      }

      // Update other filters as before
      selectedNewspaper = currentFilters.newspaper || '';
      selectedLocations = currentFilters.locations || [];
      selectedSubjects = currentFilters.subjects || [];
  }

  function applyFilters() {
    const newFilters: Filters = {};
    // Update date range based on filterStartYear and filterEndYear
    if (filterStartYear !== undefined && filterEndYear !== undefined) {
      newFilters.date_range = {
        from: `${filterStartYear}-01-01`,
        to: `${filterEndYear}-12-31`,
      };
    } else {
        // If years are undefined, clear the date range filter
        delete newFilters.date_range;
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
    
    currentFilters = newFilters; 
    dispatch('update', newFilters);
  }

  function resetFilters() {
    // Reset start/end years to the slider defaults (min/max available)
    filterStartYear = minSliderYear; 
    filterEndYear = maxSliderYear; 
    selectedNewspaper = '';
    selectedLocations = [];
    selectedSubjects = [];
    currentFilters = {}; // Clear internal representation
    dispatch('reset'); // Notify parent about reset
    dispatch('update', {}); // Trigger update with empty filters
  }

  // Reactive statement to dispatch model change event when selection changes
  $: {
    if (selectedModel) { // Ensure it has a value
      dispatch('modelchange', { model: selectedModel });
    }
  }

  // Function to handle year range change from slider
  function handleYearChange(event: CustomEvent<{ startYear: number; endYear: number }>) {
    filterStartYear = event.detail.startYear;
    filterEndYear = event.detail.endYear;
    // Optionally apply filters immediately on slider change
    // applyFilters(); 
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

  <!-- Date Range -> Year Range Slider -->
  <div class="form-section">
    <label class="input-label">Year Range</label>
    {#if minSliderYear !== undefined && maxSliderYear !== undefined}
      <YearSlider 
        minYear={minSliderYear}
        maxYear={maxSliderYear}
        startYear={filterStartYear ?? minSliderYear} 
        endYear={filterEndYear ?? maxSliderYear}
        on:change={handleYearChange}
      />
       <!-- Info text removed as it's redundant with slider labels -->
    {:else}
       <p class="no-options-text">Date range information unavailable.</p>
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