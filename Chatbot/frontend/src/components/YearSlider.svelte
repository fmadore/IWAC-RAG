<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';

  export let minYear: number = 1900;
  export let maxYear: number = new Date().getFullYear();
  export let startYear: number = minYear;
  export let endYear: number = maxYear;

  const dispatch = createEventDispatcher();

  let currentStart: number;
  let currentEnd: number;

  $: currentStart = startYear;
  $: currentEnd = endYear;

  // Calculate percentage for styling the highlight
  let startPercent: number = 0;
  let endPercent: number = 100;
  $: {
      const range = maxYear - minYear;
      if (range > 0) {
          startPercent = ((currentStart - minYear) / range) * 100;
          endPercent = ((currentEnd - minYear) / range) * 100;
      } else {
          startPercent = 0;
          endPercent = 100;
      }
  }

  function handleStartChange(event: Event) {
    const target = event.target as HTMLInputElement;
    let newStart = parseInt(target.value, 10);
    if (newStart >= currentEnd) { // Use >= to prevent exact overlap if desired
      newStart = currentEnd;
      target.value = String(newStart); 
    }
    currentStart = newStart;
    dispatchIfChanged();
  }

  function handleEndChange(event: Event) {
    const target = event.target as HTMLInputElement;
    let newEnd = parseInt(target.value, 10);
    if (newEnd <= currentStart) { // Use <= 
      newEnd = currentStart;
      target.value = String(newEnd); 
    }
    currentEnd = newEnd;
    dispatchIfChanged();
  }

  let lastDispatchedStart = startYear;
  let lastDispatchedEnd = endYear;

  function dispatchIfChanged() {
    if (currentStart !== lastDispatchedStart || currentEnd !== lastDispatchedEnd) {
      lastDispatchedStart = currentStart;
      lastDispatchedEnd = currentEnd;
      dispatch('change', { startYear: currentStart, endYear: currentEnd });
    }
  }

  onMount(() => {
      currentStart = startYear;
      currentEnd = endYear;
      lastDispatchedStart = startYear;
      lastDispatchedEnd = endYear;
      // Recalculate percentages on mount
      const range = maxYear - minYear;
      if (range > 0) {
          startPercent = ((currentStart - minYear) / range) * 100;
          endPercent = ((currentEnd - minYear) / range) * 100;
      } else {
           startPercent = 0;
           endPercent = 100;
      }
  });

</script>

<div class="year-slider-container">
  <label class="slider-label">Year Range: {currentStart} - {currentEnd}</label>
  
  <div class="sliders-wrapper">
    <!-- Background Track -->
    <div class="slider-track"></div>
    <!-- Highlighted Range -->
    <div 
        class="slider-range-highlight"
        style="--start-percent: {startPercent}%; --end-percent: {endPercent}%;"
    ></div>
    <!-- Sliders -->
    <input 
      type="range"
      aria-label="Start Year"
      min={minYear}
      max={maxYear}
      bind:value={currentStart} 
      on:input={handleStartChange} 
      class="slider slider-start"
    />
    <input 
      type="range"
      aria-label="End Year"
      min={minYear}
      max={maxYear}
      bind:value={currentEnd}
      on:input={handleEndChange} 
      class="slider slider-end"
    />
  </div>

  <div class="slider-labels">
    <span>{minYear}</span>
    <span>{maxYear}</span>
  </div>
</div>

<style>
  .year-slider-container {
    width: 100%;
    padding-bottom: 10px; 
  }

  .slider-label {
    display: block;
    font-size: 0.875rem; 
    font-weight: 500;
    margin-bottom: 0.75rem; /* Increased margin */
    color: #4a5568; 
  }

  .sliders-wrapper {
      position: relative; 
      height: 20px; 
  }

  /* Base Track Styling */
  .slider-track {
    position: absolute;
    top: 8px; /* Center vertically */
    left: 8px; /* Account for half thumb width */
    right: 8px; /* Account for half thumb width */
    height: 4px;
    background: #cbd5e0; /* Light gray track */
    border-radius: 2px;
    z-index: 0;
  }

  /* Range Highlight Styling */
  .slider-range-highlight {
    position: absolute;
    top: 8px; /* Center vertically */
    left: calc(var(--start-percent, 0%) + 8px * (1 - var(--start-percent, 0%)/100) - 8px * var(--start-percent, 0%)/100);
    right: calc(100% - var(--end-percent, 100%) + 8px * (1 - var(--end-percent, 100%)/100) - 8px * var(--end-percent, 100%)/100);
    height: 4px;
    background: #63b3ed; /* Blue highlight */
    border-radius: 2px;
    z-index: 1; /* Above track, below thumbs */
  }

  .slider {
    position: absolute; 
    top: 0;
    left: 0;
    width: 100%;
    margin: 0; 
    cursor: pointer;
    -webkit-appearance: none;
    appearance: none;
    background: transparent; /* Slider track is hidden */
    pointer-events: none; /* Only thumbs should be interactive */
    z-index: 2; /* Place sliders logically above track/highlight */
  }

  /* Remove default track styles for individual sliders */
  .slider::-webkit-slider-runnable-track {
      -webkit-appearance: none;
      height: 0;
      background: transparent;
  }
  .slider::-moz-range-track {
      -moz-appearance: none;
      height: 0;
       background: transparent;
  }

  /* Thumb Styling */
  .slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px; /* Slightly larger thumb */
    height: 18px;
    background: #4299e1; 
    border-radius: 50%;
    border: 2px solid white; /* Add border for better visibility */
    box-shadow: 0 0 2px rgba(0,0,0,0.3);
    cursor: pointer;
    pointer-events: auto; /* Thumb is interactive */
    margin-top: -7px; /* Center thumb vertically on the track height */
    position: relative; /* Needed for z-index stacking */
    z-index: 3; /* Thumbs on top */
  }

  .slider::-moz-range-thumb {
    width: 18px;
    height: 18px;
    background: #4299e1;
    border-radius: 50%;
    border: 2px solid white;
    box-shadow: 0 0 2px rgba(0,0,0,0.3);
    cursor: pointer;
    pointer-events: auto;
    position: relative;
    z-index: 3;
  }

   /* Focus Styles for Accessibility */
  .slider:focus::-webkit-slider-thumb {
    box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
  }
  .slider:focus::-moz-range-thumb {
     box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
  }

  /* Ensure end slider thumb has higher stacking priority if overlapping */
  .slider-end::-webkit-slider-thumb {
      z-index: 4;
  }
   .slider-end::-moz-range-thumb {
       z-index: 4;
   }

  .slider-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: #718096;
    margin-top: 0.25rem;
    padding: 0 8px; /* Align labels roughly with thumb centers */
  }
</style> 