// location_cascade.js — cascade country → state → city dropdowns
// Expects: window.locationData = { states: [{id,name,country_id}], cities: [{id,name,state_id}] }
document.addEventListener('DOMContentLoaded', () => {
  const countryEl = document.getElementById('countrySelect');
  const stateEl   = document.getElementById('stateSelect');
  const cityEl    = document.getElementById('citySelect');

  if (!countryEl || !stateEl || !cityEl || !window.locationData) return;

  const { states, cities } = window.locationData;

  const selectedState = parseInt(stateEl.dataset.selected || 0);
  const selectedCity  = parseInt(cityEl.dataset.selected  || 0);

  function filterStates(countryId) {
    const filtered = states.filter(s => s.country_id === countryId);
    stateEl.innerHTML = '<option value="">-- State --</option>';
    filtered.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id; opt.textContent = s.name;
      if (s.id === selectedState) opt.selected = true;
      stateEl.appendChild(opt);
    });
    filterCities(selectedState || (filtered[0] ? filtered[0].id : 0));
  }

  function filterCities(stateId) {
    const filtered = cities.filter(c => c.state_id === stateId);
    cityEl.innerHTML = '<option value="">-- City --</option>';
    filtered.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id; opt.textContent = c.name;
      if (c.id === selectedCity) opt.selected = true;
      cityEl.appendChild(opt);
    });
  }

  countryEl.addEventListener('change', e => filterStates(parseInt(e.target.value)));
  stateEl.addEventListener('change',   e => filterCities(parseInt(e.target.value)));

  // Init on load
  const initCountry = parseInt(countryEl.value);
  if (initCountry) filterStates(initCountry);
});
