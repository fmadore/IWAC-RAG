<script>
  import { createEventDispatcher } from 'svelte';

  // Props: 
  // options (object: { newspapers: [], locations: [], subjects: [], date_range: {min, max} })
  // currentFilters (object: reactive representation of active filters)
  export let options;
  export let currentFilters = {}; // Initialize as empty object

  const dispatch = createEventDispatcher();

  // Local state for inputs
  let dateFrom = currentFilters.date_range?.from || '';
  let dateTo = currentFilters.date_range?.to || '';
  let selectedNewspaper = currentFilters.newspaper || '';
  let selectedLocations = currentFilters.locations || [];
  let selectedSubjects = currentFilters.subjects || [];

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

</script>

<div class="p-2 space-y-4">
  <h3 class="text-lg font-semibold mb-3 border-b pb-2 dark:border-gray-600">Filters</h3>

  <!-- Date Range -->
  <div>
    <label class="block text-sm font-medium mb-1">Date Range</label>
    <div class="flex gap-2">
      <input type="date" bind:value={dateFrom} class="w-full p-1 border rounded text-sm dark:bg-gray-700 dark:border-gray-600" placeholder="From" aria-label="Date from">
      <input type="date" bind:value={dateTo} class="w-full p-1 border rounded text-sm dark:bg-gray-700 dark:border-gray-600" placeholder="To" aria-label="Date to">
    </div>
     {#if options.date_range && (options.date_range.min || options.date_range.max)}
       <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
         Available: {options.date_range.min || 'N/A'} to {options.date_range.max || 'N/A'}
        </p>
     {/if}
  </div>

  <!-- Newspaper -->
  <div>
    <label for="newspaper-select" class="block text-sm font-medium mb-1">Newspaper</label>
    <select id="newspaper-select" bind:value={selectedNewspaper} class="w-full p-1 border rounded text-sm dark:bg-gray-700 dark:border-gray-600">
      <option value="">All Newspapers</option>
      {#if options.newspapers}
        {#each options.newspapers as newspaper}
          <option value={newspaper}>{newspaper}</option>
        {/each}
      {/if}
    </select>
  </div>

  <!-- Locations -->
  <div>
     <label for="locations-select" class="block text-sm font-medium mb-1">Locations</label>
     {#if options.locations && options.locations.length > 0}
       <select id="locations-select" multiple bind:value={selectedLocations} class="w-full p-1 border rounded text-sm dark:bg-gray-700 dark:border-gray-600 h-24">
         <!-- <option value="">All Locations</option> --> <!-- Multiple select doesn't need an 'All' usually -->
         {#each options.locations as location}
           <option value={location}>{location}</option>
         {/each}
       </select>
       <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Hold Ctrl/Cmd to select multiple.</p>
     {:else}
        <p class="text-sm text-gray-500 dark:text-gray-400">No location filters available.</p>
     {/if}
   </div>

   <!-- Subjects -->
  <div>
     <label for="subjects-select" class="block text-sm font-medium mb-1">Subjects</label>
     {#if options.subjects && options.subjects.length > 0}
       <select id="subjects-select" multiple bind:value={selectedSubjects} class="w-full p-1 border rounded text-sm dark:bg-gray-700 dark:border-gray-600 h-24">
         {#each options.subjects as subject}
           <option value={subject}>{subject}</option>
         {/each}
       </select>
       <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Hold Ctrl/Cmd to select multiple.</p>
     {:else}
        <p class="text-sm text-gray-500 dark:text-gray-400">No subject filters available.</p>
     {/if}
   </div>

  <!-- Buttons -->
  <div class="flex justify-between pt-4 border-t dark:border-gray-600">
    <button on:click={resetFilters} class="px-3 py-1 text-sm border border-gray-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">Reset</button>
    <button on:click={applyFilters} class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">Apply</button>
  </div>
</div> 