<script>
  import { createEventDispatcher } from 'svelte';

  // Props: 
  // options (object: { newspapers: [], locations: [], subjects: [], date_range: {min, max} })
  // currentFilters (object: reactive representation of active filters)
  // selectedModel (string: the currently selected LLM model)
  export let options;
  export let currentFilters = {}; // Initialize as empty object
  export let selectedModel = 'gemma3:4b'; // Default model passed from parent

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
    const newFilters = {};
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

<div class="p-1 space-y-6 text-sm text-gray-700 dark:text-dark-text-secondary">
  <h3 class="text-xl font-semibold mb-5 border-b border-gray-200 dark:border-gray-600 pb-3 text-gray-900 dark:text-dark-text">Filters</h3>

  <!-- Model Selection -->
  <div class="space-y-2">
    <label for="model-select" class="block font-medium text-gray-800 dark:text-dark-text">Language Model</label>
    <select 
      id="model-select" 
      bind:value={selectedModel} 
      class="w-full p-2 border border-gray-300 rounded-md text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-dark-text focus:ring-primary focus:border-primary transition duration-150 ease-in-out shadow-sm"
    >
      {#each availableModels as model}
        <option value={model.id}>{model.name}</option>
      {/each}
    </select>
  </div>

  <!-- Date Range -->
  <div class="space-y-2">
    <span class="block font-medium text-gray-800 dark:text-dark-text">Date Range</span>
    <div class="flex gap-2">
      <input 
        type="date" 
        bind:value={dateFrom} 
        class="w-full p-2 border border-gray-300 rounded-md text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-dark-text focus:ring-primary focus:border-primary transition duration-150 ease-in-out shadow-sm" 
        placeholder="From" 
        aria-label="Date from"
      >
      <input 
        type="date" 
        bind:value={dateTo} 
        class="w-full p-2 border border-gray-300 rounded-md text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-dark-text focus:ring-primary focus:border-primary transition duration-150 ease-in-out shadow-sm" 
        placeholder="To" 
        aria-label="Date to"
      >
    </div>
     {#if options.date_range && (options.date_range.min || options.date_range.max)}
       <p class="text-xs text-gray-500 dark:text-dark-text-secondary mt-1">
         Available: {options.date_range.min || 'N/A'} to {options.date_range.max || 'N/A'}
        </p>
     {/if}
  </div>

  <!-- Newspaper -->
  <div class="space-y-2">
    <label for="newspaper-select" class="block font-medium text-gray-800 dark:text-dark-text">Newspaper</label>
    <select 
      id="newspaper-select" 
      bind:value={selectedNewspaper} 
      class="w-full p-2 border border-gray-300 rounded-md text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-dark-text focus:ring-primary focus:border-primary transition duration-150 ease-in-out shadow-sm"
    >
      <option value="">All Newspapers</option>
      {#if options.newspapers}
        {#each options.newspapers as newspaper}
          <option value={newspaper}>{newspaper}</option>
        {/each}
      {/if}
    </select>
  </div>

  <!-- Locations -->
  <div class="space-y-2">
     <label for="locations-select" class="block font-medium text-gray-800 dark:text-dark-text">Locations</label>
     {#if options.locations && options.locations.length > 0}
       <select 
         id="locations-select" 
         multiple 
         bind:value={selectedLocations} 
         class="w-full p-2 border border-gray-300 rounded-md text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-dark-text focus:ring-primary focus:border-primary transition duration-150 ease-in-out shadow-sm h-32"
       >
         {#each options.locations as location}
           <option value={location}>{location}</option>
         {/each}
       </select>
       <p class="text-xs text-gray-500 dark:text-dark-text-secondary mt-1">Hold Ctrl/Cmd to select multiple.</p>
     {:else}
        <p class="text-sm text-gray-500 dark:text-dark-text-secondary">No location filters available.</p>
     {/if}
   </div>

   <!-- Subjects -->
  <div class="space-y-2">
     <label for="subjects-select" class="block font-medium text-gray-800 dark:text-dark-text">Subjects</label>
     {#if options.subjects && options.subjects.length > 0}
       <select 
         id="subjects-select" 
         multiple 
         bind:value={selectedSubjects} 
         class="w-full p-2 border border-gray-300 rounded-md text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-dark-text focus:ring-primary focus:border-primary transition duration-150 ease-in-out shadow-sm h-32"
       >
         {#each options.subjects as subject}
           <option value={subject}>{subject}</option>
         {/each}
       </select>
       <p class="text-xs text-gray-500 dark:text-dark-text-secondary mt-1">Hold Ctrl/Cmd to select multiple.</p>
     {:else}
        <p class="text-sm text-gray-500 dark:text-dark-text-secondary">No subject filters available.</p>
     {/if}
   </div>

  <!-- Buttons -->
  <div class="flex justify-between items-center pt-5 border-t border-gray-200 dark:border-gray-600">
    <button 
      on:click={resetFilters} 
      class="px-4 py-2 text-sm border border-gray-400 dark:border-gray-500 rounded-md text-gray-700 dark:text-dark-text-secondary hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:focus:ring-offset-dark-surface transition-colors duration-150 ease-in-out shadow-sm"
    >
      Reset
    </button>
    <button 
      on:click={applyFilters} 
      class="px-5 py-2 text-sm bg-primary text-white font-medium rounded-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-dark-surface transition-colors duration-150 ease-in-out shadow-sm"
    >
      Apply Filters
    </button>
  </div>
</div> 