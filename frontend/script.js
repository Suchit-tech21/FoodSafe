(() => {
    'use strict';


    // =========================================================
    // GLOBAL VARIABLES
    // =========================================================

    const $ = s => document.querySelector(s);

    const $$ = s =>
        [...document.querySelectorAll(s)];

    let restaurants = [];
    let restaurantMapInstance = null;
    let restaurantMapMarkers = new Map();
    let restaurantMapData = [];
    let allRestaurantMapData = [];
    let selectedMapRestaurantId = null;

    let qrStream = null;

    let scanTimer = null;


    // =========================================================
    // BASIC HELPERS
    // =========================================================

    const esc = x =>
        String(x ?? '').replace(
            /[&<>"']/g,
            c => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            }[c])
        );


    const nowLocal = () => {

        const d = new Date();

        d.setMinutes(
            d.getMinutes()
            - d.getTimezoneOffset()
        );

        return d.toISOString().slice(0, 16);
    };


    async function api(
        url,
        options = {}
    ) {

        const r =
            await fetch(
                url,
                options
            );

        let d = {};

        try {
            d = await r.json();
        } catch {}

        if (!r.ok) {

            throw Error(
                d.error
                || `Request failed (${r.status})`
            );
        }

        return d;
    }


    // =========================================================
    // PRIVATE ADMIN NAVIGATION
    // =========================================================
    function setPrivateNav(visible) { $$('.private-nav').forEach(b=>b.classList.toggle('hidden',!visible)); const login=$('#adminLoginNav'); if(login) login.textContent=visible?'🔐 Admin':'🔐 Admin Login'; }
    async function syncPrivateAccess() { try { const me=await api('/api/auth/me'); const ok=!!(me.authenticated&&me.user&&me.user.role==='ADMIN'); setPrivateNav(ok); if($('#adminLogout'))$('#adminLogout').classList.toggle('hidden',!ok); return ok; } catch { setPrivateNav(false); return false; } }
    // =========================================================
    // NAVIGATION
    // =========================================================

    async function show(id) {
        if(['inventorySection','detailsSection'].includes(id) && !(await syncPrivateAccess())) id='adminSection';
        if(id==='restaurantManagementSection') { const isManager=await checkManagerAuth(); if(!isManager) { $('#managerLogin')?.classList.remove('hidden'); $('#managerWorkspace')?.classList.add('hidden'); loadRestaurants('',false).then(fillSelects); } }

        $$('.section').forEach(
            s =>
                s.classList.toggle(
                    'active',
                    s.id === id
                )
        );


        $$('.nav button').forEach(
            b =>
                b.classList.toggle(
                    'active',
                    b.dataset.s === id
                )
        );


        if (
            [
                'complaintSection',
                'visitSection',
                'inventorySection','detailsSection'
            ].includes(id)
        ) {

            loadRestaurants('', false)
                .then(fillSelects);
        }


        if (
            id === 'inventorySection'
        ) {

            loadInventory();
        }

        if (id === 'detailsSection') {
            loadAdminDetails();
        }


        if (
            id === 'adminSection'
        ) {

            loadAdmin();
        }


        if (
            id === 'visitSection'
        ) {

            loadVisits();
        }


        scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }


    $$('.nav button').forEach(
        b =>
            b.addEventListener(
                'click',
                () => show(b.dataset.s)
            )
    );


    // =========================================================
    // RESTAURANTS
    // =========================================================

    function fillSelects() {

        const o =
            restaurants
                .map(
                    r =>
                        `
                        <option value="${r.id}">
                            ${esc(r.name)}
                            —
                            ${esc(r.area)}
                        </option>
                        `
                )
                .join('');


        [
            'complaintRestaurant',
            'inventoryRestaurant',
            'inventoryAddRestaurant',
            'inventoryLiveRestaurant',
            'visitRestaurant',
            'qrRestaurant',
            'managerRestaurantSelect'
        ].forEach(
            id => {
                const el = $('#' + id);
                if (el) el.innerHTML = o;
            }
        );
        const addSel=$('#inventoryAddRestaurant');
        const hidden=$('#inventoryRestaurant');
        if(addSel && hidden){
            hidden.value=addSel.value || (restaurants[0]?.id || '');
            addSel.value=hidden.value;
        }
        const liveSel=$('#inventoryLiveRestaurant');
        if(liveSel && !liveSel.value && restaurants[0]) liveSel.value=String(restaurants[0].id);
    }


    async function loadRestaurants(
        q = '',
        reveal = true
    ) {

        try {

            if (reveal) {
                $('#results').classList.remove('hidden');
                const toggle = $('#showRestaurantsButton');
                if (toggle) toggle.textContent = 'Hide Restaurants';
            }

            restaurants =
                await api(
                    '/api/restaurants'
                    +
                    (
                        q
                            ? `?q=${encodeURIComponent(q)}`
                            : ''
                    )
                );

            updateRestaurantMap(restaurants, !String(q || '').trim());


            $('#searchStatus').textContent =
                restaurants.length
                    ? `${restaurants.length} establishment(s) found.`
                    : 'No restaurants found.';


            $('#results').innerHTML =
                restaurants.length

                    ? restaurants
                        .map(
                            r =>
                                `
                                <article class="card">

                                    <img class="restaurant-image" src="${esc(r.image_url || `/images/restaurants/fallback-${Number(r.id)}.svg`)}" alt="Illustrative image for ${esc(r.name)}" loading="lazy" onerror="this.onerror=null;this.src='/images/restaurants/fallback-${Number(r.id)}.svg'">

                                    <div class="row">

                                        <div>

                                            <h3>
                                                ${esc(r.name)}
                                            </h3>

                                            <span class="small">
                                                ${esc(r.area)}
                                            </span>

                                        </div>

                                        <span
                                            class="badge ${r.risk_level.toLowerCase()}"
                                        >
                                            ${esc(r.risk_level)}
                                        </span>

                                    </div>

                                    <div class="score">

                                        ${r.risk}

                                        <span class="small">
                                            /100
                                        </span>

                                    </div>

                                    <div class="small">

                                        ${r.cuisine ? `<b>${esc(r.cuisine)}</b> · ` : ''}
                                        ${r.popular_food ? `Popular: ${esc(r.popular_food)} · ` : ''}
                                        ${r.price_range ? `${esc(r.price_range)}<br>` : ''}

                                        License
                                        ${esc(r.license_status)}

                                        ·

                                        ${r.violations}
                                        confirmed violation(s)

                                        ·

                                        ${r.verified_reports}
                                        verified report(s)

                                    </div>

                                    <button
                                        class="outline"
                                        data-profile="${r.id}"
                                    >
                                        View Safety Profile →
                                    </button>

                                </article>
                                `
                        )
                        .join('')

                    : `
                        <div class="notice">
                            No restaurants found.
                            Try Green Leaf, Kothrud,
                            Baner or Hinjewadi.
                        </div>
                    `;


            fillSelects();

            const query = String(q || '').trim().toLowerCase();
            if (query && restaurants.length) {
                const exact = restaurants.find(r => String(r.name || '').toLowerCase() === query);
                const starts = restaurants.find(r => String(r.name || '').toLowerCase().startsWith(query));
                const match = exact || (restaurants.length === 1 ? restaurants[0] : starts);
                if (match) profile(Number(match.id));
            }

        } catch (e) {

            $('#results').innerHTML =
                `
                <div class="notice error">
                    FoodSafe service is unavailable.
                    Please check that the backend is running.
                </div>
                `;
        }
    }


    // =========================================================
    // FREE RESTAURANT MAP + SIMULATED PROTOTYPE RATINGS
    // Ratings are intentionally labelled as demo data. They are not
    // fetched from Google and must not be presented as real reviews.
    // =========================================================
    function prototypeRating(id) {
        // Stable illustrative values (3.6–4.9) for repeatable demos.
        return (3.6 + (((Number(id) * 37) % 14) / 10)).toFixed(1);
    }

    function mapCoordinates(r) {
        let lat = Number(r.latitude), lng = Number(r.longitude);
        if (Number.isFinite(lat) && Number.isFinite(lng) && lat && lng) {
            return { lat, lng, approximate: false };
        }
        // Approximate neighborhood pins for the two records without coordinates.
        const area = String(r.area || '').toLowerCase();
        if (area.includes('camp')) return { lat: 18.5132, lng: 73.8790, approximate: true };
        if (area.includes('pune')) return { lat: 18.5140, lng: 73.8790, approximate: true };
        return { lat: 18.5204, lng: 73.8567, approximate: true };
    }

    function googleMapsSearchUrl(r) {
        const c = mapCoordinates(r);
        const query = `${r.name || ''} ${r.area || ''} Pune`;
        return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}&query_place_id=`;
    }

    function selectRestaurantOnMap(id, pan = true) {
        const r = restaurantMapData.find(x => Number(x.id) === Number(id));
        if (!r) return;
        selectedMapRestaurantId = Number(r.id);
        const c = mapCoordinates(r);
        // Schematic map has no external map instance; selection is shown by the active pin.
        const rating = prototypeRating(r.id);
        const risk = Number(r.risk ?? 0);
        const googleUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${r.name} ${r.area || ''} Pune`)}`;
        const detail = $('#mapSelectedDetails');
        if (detail) detail.innerHTML = `
            <div class="selected-map-title"><span class="selected-map-pin">📍</span><div><h3>${esc(r.name)}</h3><p>${esc(r.area || 'Pune')}</p></div></div>
            <div class="map-rating-line"><span class="map-stars" aria-label="${rating} out of 5 stars">★ ${rating}<small>/5</small></span><span class="demo-tag">SIMULATED RATING</span></div>
            <div class="map-score-row"><span>FoodSafe risk score</span><strong>${esc(risk)}<small>/100</small></strong></div>
            <p class="map-disclaimer">Illustrative customer rating for the prototype only. Not sourced from Google or actual customer reviews.</p>
            ${c.approximate ? '<p class="approx-location-note">ⓘ Approximate neighborhood location</p>' : ''}
            <a class="map-google-link" href="${googleUrl}" target="_blank" rel="noopener noreferrer">Open in Google Maps ↗</a>
            <button class="outline map-profile-button" type="button" data-map-profile="${Number(r.id)}">View FoodSafe Safety Profile →</button>`;
        $$('#restaurantMapList .map-restaurant-item').forEach(el => el.classList.toggle('selected', Number(el.dataset.mapId) === Number(r.id)));
        updateRestaurantMap(restaurantMapData);
        $$('#restaurantMapList .map-restaurant-item').forEach(el => el.classList.toggle('selected', Number(el.dataset.mapId) === Number(r.id)));
    }

    function updateRestaurantMap(rows, replaceAll = false) {
        if (!Array.isArray(rows)) return;
        if (replaceAll || !allRestaurantMapData.length) allRestaurantMapData = rows.slice();
        restaurantMapData = rows.slice();
        const list = $('#restaurantMapList');
        const count = $('#mapResultCount');
        if (count) count.textContent = `${rows.length} location${rows.length === 1 ? '' : 's'}`;
        if (list) {
            list.innerHTML = rows.length ? rows.map(r => {
                const rating = prototypeRating(r.id);
                const c = mapCoordinates(r);
                return `<button type="button" class="map-restaurant-item ${Number(r.id) === selectedMapRestaurantId ? 'selected' : ''}" data-map-id="${Number(r.id)}">
                    <span class="map-item-marker">${Number(r.id)}</span><span class="map-item-copy"><strong>${esc(r.name)}</strong><small>${esc(r.area || 'Pune')}${c.approximate ? ' · approximate pin' : ''}</small><span class="map-item-rating">★ ${rating} <em>demo rating</em></span></span><span class="map-item-chevron">›</span>
                </button>`;
            }).join('') : '<p class="map-empty">No restaurants match your search.</p>';
        }
        // Local schematic map: no external tile server, API key, or map library required.
        const map = $('#restaurantMap');
        if (!map) return;
        map.classList.add('foodsafe-schematic-map');
        const pinMarkup = rows.map((r, i) => {
            // Distribute markers across a stylized Pune map so every demo restaurant is visible.
            const x = 9 + ((i * 29 + 13) % 82);
            const y = 12 + ((i * 43 + 17) % 74);
            const rating = prototypeRating(r.id);
            return `<button type="button" class="schematic-pin ${Number(r.id) === selectedMapRestaurantId ? 'active' : ''}" style="left:${x}%;top:${y}%" data-map-id="${Number(r.id)}" data-restaurant-name="${esc(r.name)}" aria-label="${esc(r.name)} — rating ${rating} out of 5" title="${esc(r.name)} — ★ ${rating}"><span aria-hidden="true">🍽</span><span class="schematic-pin-tooltip">${esc(r.name)}</span></button>`;
        }).join('');
        map.innerHTML = `<div class="schematic-map-art" aria-label="Illustrative map of Pune with restaurant locations">
            <div class="map-waterway"></div><div class="map-park park-one"></div><div class="map-park park-two"></div>
            <div class="map-road road-a"></div><div class="map-road road-b"></div><div class="map-road road-c"></div><div class="map-road road-d"></div><div class="map-road road-e"></div><div class="map-road road-f"></div><div class="map-road road-g"></div>
            <span class="map-place place-pune">PUNE</span><span class="map-place place-camp">CAMP</span><span class="map-place place-kothrud">KOTHRUD</span><span class="map-place place-shivaji">SHIVAJI NAGAR</span><span class="map-place place-hadapsar">HADAPSAR</span>
            ${pinMarkup}
            <div class="schematic-map-caption"><span class="map-legend-dot"></span> ${rows.length} FoodSafe demo restaurant${rows.length === 1 ? '' : 's'} <span>· Schematic view, not navigation-grade geography</span></div>
        </div>`;
        if (rows.length && selectedMapRestaurantId && rows.some(r => Number(r.id) === selectedMapRestaurantId)) {
            // Keep the selected restaurant highlighted after filtering.
            const active = map.querySelector(`.schematic-pin[data-map-id="${selectedMapRestaurantId}"]`);
            if (active) active.classList.add('active');
        }
    }

    $('#restaurantMapSearch')?.addEventListener('input', event => {
        const q = String(event.target.value || '').trim().toLowerCase();
        const filtered = allRestaurantMapData.filter(r => `${r.name || ''} ${r.area || ''} ${r.cuisine || ''}`.toLowerCase().includes(q));
        // Re-render from the full local dataset; this is independent of the main consumer search.
        updateRestaurantMap(filtered);
    });
    $('#resetRestaurantMap')?.addEventListener('click', async () => {
        const input = $('#restaurantMapSearch'); if (input) input.value = '';
        try { const all = await api('/api/restaurants'); updateRestaurantMap(all, true); }
        catch { updateRestaurantMap(restaurants); }
        selectedMapRestaurantId = null;
        if (restaurantMapInstance) restaurantMapInstance.setView([18.5204, 73.8567], 12);
    });
    document.addEventListener('click', event => {
        const item = event.target.closest('[data-map-id]');
        if (item) selectRestaurantOnMap(Number(item.dataset.mapId));
        const profileButton = event.target.closest('[data-map-profile]');
        if (profileButton) profile(Number(profileButton.dataset.mapProfile));
    });

    $('#showRestaurantsButton')?.addEventListener('click', async () => {
        const results = $('#results');
        const button = $('#showRestaurantsButton');

        if (!results.classList.contains('hidden')) {
            results.classList.add('hidden');
            button.textContent = 'Show Restaurants';
            $('#searchStatus').textContent = 'Restaurant list hidden. Search by name or use photo search.';
            return;
        }

        button.textContent = 'Hide Restaurants';
        await loadRestaurants('', true);
    });


    $('#searchButton')
        .addEventListener(
            'click',
            () =>
                loadRestaurants(
                    $('#searchInput').value
                )
        );


    $('#searchInput')
        .addEventListener(
            'keydown',
            e => {

                if (e.key === 'Enter') {

                    loadRestaurants(
                        e.target.value
                    );
                }
            }
        );


    $('#results')
        .addEventListener(
            'click',
            e => {

                const b =
                    e.target.closest(
                        '[data-profile]'
                    );

                if (b) {

                    profile(
                        Number(
                            b.dataset.profile
                        )
                    );
                }
            }
        );


    async function profile(id) {

        try {

            const [
                r,
                k,
                p
            ] =
                await Promise.all([

                    api(
                        `/api/restaurants/${id}`
                    ),

                    api(
                        `/api/restaurants/${id}/risk`
                    ),

                    api(
                        `/api/restaurants/${id}/provenance`
                    )

                ]);


            $('#profile').innerHTML =
                `
                <button class="profile-close" type="button" id="closeProfile" aria-label="Close restaurant details" title="Close restaurant details">×</button>
                <div class="row">

                    <div>

                        <small>
                            FOOD SAFETY PROFILE
                        </small>

                        <h2>
                            ${esc(r.name)}
                        </h2>

                        <p>

                            ${esc(r.area)}

                            ·

                            <b>
                                Demo/prototype record
                            </b>

                        </p>

                    </div>

                    <span
                        class="badge ${k.level.toLowerCase()}"
                    >
                        ${k.level}
                    </span>

                </div>


                <img class="profile-image" src="${esc(r.image_url || `/images/restaurants/fallback-${Number(r.id)}.svg`)}" alt="Illustrative image for ${esc(r.name)}" onerror="this.onerror=null;this.src='/images/restaurants/fallback-${Number(r.id)}.svg'">

                <div class="profile-details">
                    ${r.address ? `<div><b>Address:</b> ${esc(r.address)}</div>` : ''}
                    ${r.cuisine ? `<div><b>Cuisine:</b> ${esc(r.cuisine)}</div>` : ''}
                    ${r.popular_food ? `<div><b>Popular:</b> ${esc(r.popular_food)}</div>` : ''}
                    ${r.price_range ? `<div><b>Price:</b> ${esc(r.price_range)}</div>` : ''}
                    ${r.phone ? `<div><b>Phone:</b> ${esc(r.phone)}</div>` : ''}
                </div>


                <div class="score">

                    ${k.score}

                    <span class="small">
                        /100
                    </span>

                </div>


                <div class="profilegrid">

                    ${
                        [
                            [
                                'License',
                                '✓ ' + r.license_status
                            ],
                            [
                                'Inspection',
                                '✓ ' + r.inspection
                            ],
                            [
                                'Confirmed Violations',
                                '⚠ ' + r.violations
                            ],
                            [
                                'Verified Reports',
                                '⚠ ' + r.verified_reports
                            ],
                            [
                                'Pending Reports',
                                r.pending_reports
                            ],
                            [
                                'Inventory Incidents',
                                r.inventory_incidents
                            ]
                        ]
                        .map(
                            x =>
                                `
                                <div class="metric">

                                    ${x[0]}

                                    <b>
                                        ${esc(x[1])}
                                    </b>

                                </div>
                                `
                        )
                        .join('')
                    }

                </div>


                <div class="notice">

                    <h3>
                        Why this indicator?
                    </h3>

                    ${
                        k.factors
                            .map(
                                f =>
                                    `
                                    <div class="factor">

                                        <span>

                                            ${
                                                f.impact === 'positive'
                                                    ? '＋'
                                                    : '−'
                                            }

                                            ${esc(f.name)}

                                            (${esc(f.value)})

                                        </span>

                                        <b
                                            class="${f.impact}"
                                        >

                                            ${
                                                f.points > 0
                                                    ? '+'
                                                    : ''
                                            }${f.points}

                                        </b>

                                    </div>
                                    `
                            )
                            .join('')
                    }


                    <p class="small">
                        ${esc(k.explanation)}
                    </p>

                </div>


                <div class="notice">

                    <h3>
                        Trust & Provenance
                    </h3>

                    <p class="small">
                        Public reports are not equivalent
                        to official violations.
                    </p>

                    <div class="prov">

                        ${
                            p.map(
                                x =>
                                    `
                                    <div class="provitem">

                                        <b>
                                            ${esc(x.type)}
                                        </b>

                                        <h3>
                                            ${esc(x.title)}
                                        </h3>

                                        <span class="small">

                                            Source:
                                            ${esc(x.source)}

                                            <br>

                                            Verification:
                                            ${esc(
                                                x.verification_status
                                            )}

                                            <br>

                                            Evidence:
                                            ${esc(x.evidence)}

                                            <br>

                                            ${esc(x.timestamp)}

                                        </span>


                                        ${
                                            x.source_reference
                                                ? `
                                                    <div class="small">
                                                        Reference:
                                                        ${esc(
                                                            x.source_reference
                                                        )}
                                                    </div>
                                                  `
                                                : ''
                                        }

                                    </div>
                                    `
                            )
                            .join('')
                        }

                    </div>

                </div>
                `;


            $('#profile')
                .scrollIntoView({
                    behavior: 'smooth'
                });

        } catch (e) {

            $('#profile').innerHTML =
                `
                <div class="notice error">
                    ${esc(e.message)}
                </div>
                `;
        }
    }


    $('#profile')?.addEventListener('click', e => {
        if (e.target.closest('#closeProfile')) {
            $('#profile').innerHTML = '';
            $('#searchInput').focus();
        }
    });

    // =========================================================
    // COMPLAINTS
    // =========================================================

    $('#severity')
        .addEventListener(
            'input',
            e =>
                $('#severityValue').value =
                    e.target.value
        );


    $('#complaintTimestamp').value =
        nowLocal();


    $('#complaintForm')
        .addEventListener(
            'submit',
            async e => {

                e.preventDefault();

                const btn =
                    e.submitter;

                btn.disabled = true;

                try {

                    const d =
                        await api(
                            '/api/complaints',
                            {
                                method: 'POST',
                                body:
                                    new FormData(
                                        e.target
                                    )
                            }
                        );


                    $('#complaintResult').innerHTML =
                        `
                        <div class="notice success">

                            <b>
                                ✓ Complaint Submitted
                            </b>

                            <br>

                            Complaint ID:
                            <strong>
                                ${esc(d.id)}
                            </strong>

                            <br>

                            Verification:
                            <strong>
                                ${esc(
                                    d.verification_status
                                )}
                            </strong>

                            <br>

                            Priority:
                            <strong>
                                ${esc(d.priority)}
                            </strong>

                            · Score
                            ${d.priority_score}

                            <br>

                            Timestamp:
                            ${esc(d.timestamp)}

                        </div>
                        `;


                    e.target.reset();

                    $('#severity').value = 5;

                    $('#severityValue').value = 5;

                    $('#complaintTimestamp')
                        .value = nowLocal();

                } catch (x) {

                    $('#complaintResult').innerHTML =
                        `
                        <div class="notice error">
                            ${esc(x.message)}
                        </div>
                        `;

                } finally {

                    btn.disabled = false;
                }
            }
        );


    // =========================================================
    // INVENTORY
    // =========================================================
    let inventoryCache=[];let inventoryFilter='ALL';
    const inventoryStatusClass=status=>status==='EXPIRED'?'high':(status==='EXPIRING SOON'||status==='LOW STOCK')?'moderate':'low';
    function renderInventorySummary(d){if(!$('#inventorySummary'))return;$('#inventorySummary').innerHTML=[['📦','Total Items',d.total_items],['🟢','Safe',d.safe],['🟡','Low Stock',d.low_stock],['⏳','Expiring Soon',d.expiring],['🔴','Expired',d.expired],['⚠️','Incidents',d.incidents]].map(x=>`<div class="inventory-stat"><span>${x[0]}</span><small>${x[1]}</small><b>${x[2]}</b></div>`).join('');}
    function renderInventory(){const d=inventoryFilter==='ALL'?inventoryCache:inventoryCache.filter(x=>x.status===inventoryFilter);$('#inventoryList').innerHTML=d.map(x=>`<div class="inventory-card"><div class="inventory-icon">${esc(x.icon||'🍽️')}</div><div class="inventory-main"><div class="row"><div><b>${esc(x.product)}</b><div class="small">${esc(x.category||'Other')}</div></div><span class="badge ${inventoryStatusClass(x.status)}">${esc(x.status)}</span></div><div class="inventory-meta"><span>📦 ${esc(x.batch_number||'—')}</span><span>⚖️ ${esc(x.quantity)} ${esc(x.unit||'')}</span><span>📅 ${esc(x.expiry_date)}</span><span>🏪 ${esc(x.supplier||'—')}</span><span>❄️ ${esc(x.storage_condition||'Ambient')}</span></div>${x.incident_type&&x.incident_type!=='NONE'?`<div class="incident-chip">⚠️ ${esc(x.incident_type)}</div>`:''}${x.notes?`<div class="small">${esc(x.notes)}</div>`:''}</div></div>`).join('')||'<div class="notice">No inventory items match this filter.</div>';}
    async function loadInventory(restaurantId){try{
        const rid=restaurantId || $('#inventoryLiveRestaurant')?.value;
        if(!rid){$('#inventoryList').innerHTML='<div class="notice">Select a restaurant to view live stock.</div>';return;}
        const[d,summary]=await Promise.all([api('/api/inventory?restaurant_id='+encodeURIComponent(rid)),api('/api/inventory/summary?restaurant_id='+encodeURIComponent(rid))]);
        inventoryCache=d;renderInventorySummary(summary);renderInventory();
        const r=restaurants.find(x=>String(x.id)===String(rid));
        if($('#liveStockTitle')) $('#liveStockTitle').textContent=`${r?r.name:'Restaurant'} — Live Stock`;
        const top=d.find(x=>x.is_earliest);$('#heapCallout').className='heapcall';$('#heapCallout').innerHTML=top?`<b>MIN HEAP</b> → Earliest Expiry: <strong>${esc(top.icon||'🍽️')} ${esc(top.product)}</strong> · ${top.days_remaining<0?Math.abs(top.days_remaining)+' day(s) overdue':top.days_remaining+' day(s) remaining'}`:'MIN HEAP → No inventory';
    }catch(e){$('#inventoryList').innerHTML=`<div class="notice error">Unable to load inventory: ${esc(e.message)}</div>`;}}
    $('#inventoryFilters')?.addEventListener('click',e=>{const b=e.target.closest('[data-filter]');if(!b)return;inventoryFilter=b.dataset.filter;$$('#inventoryFilters button').forEach(x=>x.classList.toggle('active-filter',x===b));renderInventory();});
    $('#inventoryAddRestaurant')?.addEventListener('change',e=>{const h=$('#inventoryRestaurant');if(h)h.value=e.target.value;});
    $('#inventoryLiveRestaurant')?.addEventListener('change',e=>{inventoryFilter='ALL';$$('#inventoryFilters button').forEach(x=>x.classList.toggle('active-filter',x.dataset.filter==='ALL'));loadInventory(e.target.value);});
    $('#inventoryForm')?.addEventListener('submit',async e=>{e.preventDefault();try{const d=Object.fromEntries(new FormData(e.target));d.restaurant_id=Number($('#inventoryAddRestaurant')?.value||d.restaurant_id); d.quantity=+d.quantity;d.reorder_level=+d.reorder_level;d.restaurant_id=+d.restaurant_id;await api('/api/inventory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});e.target.reset();$('#inventoryResult').innerHTML='<div class="notice success">Inventory item added to the dedicated inventory database.</div>';await loadInventory();}catch(x){$('#inventoryResult').innerHTML=`<div class="notice error">${esc(x.message)}</div>`;}});
    $('#inventoryModeTabs')?.addEventListener('click',e=>{const b=e.target.closest('[data-inventory-mode]');if(!b)return;const mode=b.dataset.inventoryMode;$$('#inventoryModeTabs button').forEach(x=>x.classList.toggle('active',x===b));$('#inventoryAddPanel').classList.toggle('hidden',mode!=='add');$('#inventoryLivePanel').classList.toggle('hidden',mode!=='live');if(mode==='live')loadInventory($('#inventoryLiveRestaurant')?.value);});
    $('#adminModeTabs')?.addEventListener('click',e=>{const b=e.target.closest('[data-admin-mode]');if(!b)return;const mode=b.dataset.adminMode;$$('#adminModeTabs button').forEach(x=>x.classList.toggle('active',x===b));[['overview','adminOverviewPanel'],['risk','adminRiskPanel'],['priority','adminPriorityPanel'],['reports','adminReportsPanel'],['expiry','adminExpiryPanel']].forEach(([m,id])=>$('#'+id)?.classList.toggle('hidden',m!==mode));if(mode==='reports')loadIssuedReports();});
    $('#riskFilters')?.addEventListener('click',e=>{const b=e.target.closest('[data-risk-filter]');if(!b)return;$$('#riskFilters button').forEach(x=>x.classList.toggle('active',x===b));renderRiskOverview(b.dataset.riskFilter);});


    // =========================================================
    // RESTAURANT MANAGEMENT LOGIN + SCOPED INVENTORY
    // =========================================================
    let managerActive = false;
    async function loadManagerInventory() {
      const host=$('#managerInventoryList'); if(!host)return; host.innerHTML='<div class="notice">Loading your restaurant stock…</div>';
      try { const d=await api('/api/restaurant-management/inventory'); const s=d.summary||{};
        $('#managerInventorySummary').innerHTML=[['📦','Total Items',s.total_items||0],['🟢','Safe',s.safe||0],['🟡','Low Stock',s.low_stock||0],['⏳','Expiring',s.expiring||0],['🔴','Expired',s.expired||0]].map(x=>`<div class="inventory-stat"><span>${x[0]}</span><small>${x[1]}</small><b>${x[2]}</b></div>`).join('');
        host.innerHTML=(d.items||[]).map(x=>`<div class="inventory-card"><div class="inventory-icon">${esc(x.icon||'🍽️')}</div><div class="inventory-main"><div class="row"><div><b>${esc(x.product)}</b><div class="small">${esc(x.category||'Other')} · Batch ${esc(x.batch_number||'—')}</div></div><span class="badge ${x.status==='EXPIRED'?'high':(['LOW STOCK','EXPIRING SOON'].includes(x.status)?'moderate':'low')}">${esc(x.status)}</span></div><div class="inventory-meta"><span>Quantity: ${esc(x.quantity)} ${esc(x.unit||'')}</span><span>Expiry: ${esc(x.expiry_date||'—')}</span><span>Supplier: ${esc(x.supplier||'—')}</span><span>Storage: ${esc(x.storage_condition||'Ambient')}</span></div>${x.notes?`<p class="small">${esc(x.notes)}</p>`:''}</div></div>`).join('')||'<div class="notice">No stock items recorded for this restaurant yet. Use Add Stock below.</div>';
      } catch(e) { host.innerHTML=`<div class="notice error">${esc(e.message)}</div>`; }
    }
    async function checkManagerAuth() {
      try { const me=await api('/api/restaurant-management/me'); managerActive=true; $('#managerLogin').classList.add('hidden'); $('#managerWorkspace').classList.remove('hidden'); $('#managerRestaurantName').textContent=`${me.restaurant} (${me.area||''})`; await loadManagerInventory(); return true; }
      catch { managerActive=false; $('#managerLogin')?.classList.remove('hidden'); $('#managerWorkspace')?.classList.add('hidden'); return false; }
    }
    $('#managerLoginForm')?.addEventListener('submit', async e=>{ e.preventDefault(); const result=$('#managerLoginResult'); result.textContent='Signing in…';
      try { const r=await api('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:$('#managerLoginUser').value,password:$('#managerLoginPass').value,restaurant_id:$('#managerRestaurantSelect').value})});
        if(r.user.role!=='BUSINESS') throw Error('This account is not a restaurant management account.');
        result.innerHTML='<span class="ok">Restaurant workspace opened.</span>'; await checkManagerAuth(); show('restaurantManagementSection');
      } catch(err) { result.innerHTML=`<span class="error">${esc(err.message)}</span>`; }
    });
    $('#managerLogout')?.addEventListener('click',async()=>{try{await api('/api/auth/logout',{method:'POST'});}catch{} managerActive=false; $('#managerWorkspace').classList.add('hidden'); $('#managerLogin').classList.remove('hidden'); $('#managerLoginPass').value=''; $('#managerLoginResult').innerHTML='<div class="notice">You have been logged out.</div>'; show('restaurantManagementSection');});
    $('#managerRefreshInventory')?.addEventListener('click',loadManagerInventory);
    $('#managerInventoryForm')?.addEventListener('submit',async e=>{e.preventDefault();try{const d=Object.fromEntries(new FormData(e.target));d.quantity=Number(d.quantity);d.reorder_level=Number(d.reorder_level);await api('/api/restaurant-management/inventory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});$('#managerInventoryResult').innerHTML='<div class="notice success">Stock added to this restaurant only.</div>';e.target.reset();await loadManagerInventory();}catch(err){$('#managerInventoryResult').innerHTML=`<div class="notice error">${esc(err.message)}</div>`;}});

    // =========================================================
    // ADMIN AUTHENTICATION
    // =========================================================

    async function checkAdminAuth() {
        const me = await api('/api/auth/me');
        const ok = !!(me.authenticated && me.user && me.user.role === 'ADMIN');
        if (ok) {
            $('#adminLogin').classList.add('hidden');
            $('#adminWorkspace').classList.remove('hidden');
            $('#adminWelcome').textContent = me.user.display_name || me.user.username || 'Admin';
            setPrivateNav(true);
            return true;
        }
        $('#adminLogin').classList.remove('hidden');
        $('#adminWorkspace').classList.add('hidden');
        setPrivateNav(false);
        return false;
    }

    $('#loginForm')?.addEventListener(
        'submit',
        async e => {

            e.preventDefault();

            try {

                const r =
                    await api(
                        '/api/auth/login',
                        {
                            method: 'POST',

                            headers: {
                                'Content-Type':
                                    'application/json'
                            },

                            body:
                                JSON.stringify({
                                    username:
                                        $('#loginUser')
                                            .value,

                                    password:
                                        $('#loginPass')
                                            .value
                                })
                        }
                    );


                $('#loginResult').innerHTML =
                    `
                    <span class="ok">

                        Logged in as
                        ${esc(
                            r.user.display_name
                        )}

                        (
                        ${esc(r.user.role)}
                        )

                    </span>
                    `;


                $('#adminLogin').classList.add('hidden');$('#adminWorkspace').classList.remove('hidden');setPrivateNav(true);$('#adminWelcome').textContent=r.user.display_name||r.user.username||'Admin';show('adminSection');loadAdmin();

            } catch (err) {

                $('#loginResult').innerHTML =
                    `
                    <span class="error">
                        ${esc(err.message)}
                    </span>
                    `;
            }
        }
    );


    $('#adminLogout')?.addEventListener('click',async()=>{try{await api('/api/auth/logout',{method:'POST'});}catch{}setPrivateNav(false);$('#adminLogin').classList.remove('hidden');$('#adminWorkspace').classList.add('hidden');$('#loginUser').value='';$('#loginPass').value='';$('#loginResult').innerHTML='<div class="notice">You have been logged out.</div>';show('adminSection');});

    // =========================================================
    // ADMIN COMPLAINT MODERATION
    // =========================================================

    async function reviewComplaint(
        cid,
        decision
    ) {

        const remarks =
            prompt(
                'Reviewer remarks (optional):',
                'Reviewed against submitted evidence'
            );


        if (
            remarks === null
        ) {
            return;
        }


        try {

            await api(
                '/api/admin/complaints/'
                +
                encodeURIComponent(cid)
                +
                '/review',
                {
                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body:
                        JSON.stringify({
                            decision,
                            remarks
                        })
                }
            );


            loadAdmin();
            if ($('#adminReportsPanel') && !$('#adminReportsPanel').classList.contains('hidden')) loadIssuedReports();

        } catch (e) {

            alert(
                e.message
            );
        }
    }


    let issuedReportsCache = [];
    function renderIssuedReports() {
        const host = $('#adminIssuedReports'); if (!host) return;
        const query = ($('#reportSearchFilter')?.value || '').trim().toLowerCase();
        const status = $('#reportStatusFilter')?.value || 'ALL';
        const filtered = issuedReportsCache.filter(c => {
            const s = String(c.verification_status || 'PENDING').toUpperCase();
            const matchesStatus = status === 'ALL' || s === status;
            const hay = `${c.id||''} ${c.restaurant||''} ${c.description||''} ${c.category||''}`.toLowerCase();
            return matchesStatus && (!query || hay.includes(query));
        });
        host.innerHTML = filtered.map((c, index) => `
          <article class="case issued-report-card report-summary-card">
            <div class="row"><div><small>REPORT ${esc(c.id)}</small><h3>${esc(c.restaurant || 'Restaurant')}</h3><div class="meta">${esc(c.area || '')} · ${esc(c.timestamp || '')}</div></div><span class="report-status">${esc(c.verification_status || 'PENDING')}</span></div>
            <p><b>${esc(c.category || 'Other')}</b> · Severity ${esc(c.severity || '—')}/10</p>
            <p class="report-summary-text">${esc((c.description || 'No description supplied').slice(0,170))}${(c.description||'').length>170?'…':''}</p>
            <button type="button" class="primary" data-evaluate-report="${esc(c.id)}">${String(c.verification_status).toUpperCase()==='PENDING'?'Evaluate this report':'View report details'}</button>
            <div class="report-evaluation-details hidden" id="report-detail-${esc(c.id)}">
              <div class="report-detail-grid"><div><b>Problem faced</b><p>${esc(c.description || 'No description supplied')}</p></div><div><b>Category / Severity</b><p>${esc(c.category || 'Other')} · ${esc(c.severity || '—')}/10</p><b>Location</b><p>${esc(c.location || 'Not provided')}</p><b>Bill / reference</b><p>${esc(c.bill_reference || 'Not provided')}</p></div></div>
              <div class="report-evidence-grid">
                <div class="report-evidence"><b>📷 Uploaded evidence photo</b>${c.evidence_path ? `<a href="/api/admin/reports/${encodeURIComponent(c.id)}/evidence" target="_blank" rel="noopener"><img src="/api/admin/reports/${encodeURIComponent(c.id)}/evidence" alt="Evidence photo for ${esc(c.id)}"></a><a href="/api/admin/reports/${encodeURIComponent(c.id)}/evidence" target="_blank" rel="noopener">Open full-size photo</a>` : '<p class="small">No evidence photo was uploaded.</p>'}</div>
                <div class="report-evidence"><b>🧾 Bill / receipt</b>${c.bill_evidence_path ? `<a href="/api/admin/reports/${encodeURIComponent(c.id)}/bill" target="_blank" rel="noopener"><img src="/api/admin/reports/${encodeURIComponent(c.id)}/bill" alt="Bill evidence for ${esc(c.id)}"></a><a href="/api/admin/reports/${encodeURIComponent(c.id)}/bill" target="_blank" rel="noopener">Open bill / receipt</a>` : `<p class="small">${c.bill_reference ? `Reference: ${esc(c.bill_reference)}` : 'No bill image or reference supplied.'}</p>`}</div>
              </div>
              <div class="report-review-history"><b>📝 Review history</b>${c.review_history && c.review_history.length ? c.review_history.map(v=>`<div class="case"><b>${esc(v.decision)}</b> · ${esc(v.reviewer)} · ${esc(v.timestamp)}<p>${esc(v.remarks || 'No reviewer remarks')}</p></div>`).join('') : '<p class="small">No review has been recorded yet.</p>'}</div>
              ${String(c.verification_status).toUpperCase()==='PENDING' ? `<div class="report-actions"><button type="button" onclick="reviewComplaint('${esc(c.id)}','VERIFY')">✓ Verify Report</button><button type="button" class="secondary" onclick="reviewComplaint('${esc(c.id)}','REJECT')">✕ Reject Report</button></div>` : ''}
            </div>
          </article>`).join('') || '<div class="notice">No reports match these filters.</div>';
    }
    async function loadIssuedReports() {
        const host = $('#adminIssuedReports'); if (!host) return;
        host.innerHTML = '<div class="notice">Loading issued reports…</div>';
        try { issuedReportsCache = await api('/api/admin/reports'); renderIssuedReports(); }
        catch (e) { host.innerHTML = `<div class="notice error">Could not load reports: ${esc(e.message)}</div>`; }
    }
    $('#reportSearchFilter')?.addEventListener('input', renderIssuedReports);
    $('#reportStatusFilter')?.addEventListener('change', renderIssuedReports);
    $('#adminIssuedReports')?.addEventListener('click', e => {
        const b=e.target.closest('[data-evaluate-report]'); if(!b)return;
        const panel=$('#report-detail-'+CSS.escape(b.dataset.evaluateReport)); if(!panel)return;
        const open=panel.classList.contains('hidden'); panel.classList.toggle('hidden',!open);
        b.textContent=open?'Hide evaluation details':(String(issuedReportsCache.find(x=>String(x.id)===b.dataset.evaluateReport)?.verification_status).toUpperCase()==='PENDING'?'Evaluate this report':'View report details');
        if(open) panel.scrollIntoView({behavior:'smooth',block:'nearest'});
    });
    $('#refreshReportsButton')?.addEventListener('click', loadIssuedReports);

    window.reviewComplaint = reviewComplaint;

    // =========================================================
    // ADMIN DASHBOARD
    // =========================================================

    function renderRiskOverview(filter='ALL') {
        const list = window.__riskOverview || [];
        const filtered = list.filter(r => filter==='ALL' || (filter==='SAFE' ? String(r.risk.level).toUpperCase()==='LOW' : filter==='MEDIUM' ? String(r.risk.level).toUpperCase()==='MODERATE' : String(r.risk.level).toUpperCase()==='HIGH'));
        $('#adminRiskTable').innerHTML = filtered.map(r=>`<div class="risk-row"><div><b>${esc(r.name)}</b><span>${esc(r.area)}</span></div><span class="badge ${String(r.risk.level).toLowerCase()}">${esc(r.risk.level)}</span><strong>${Math.round(r.risk.score)}/100</strong></div>`).join('')||'<div class="notice">No restaurants match this risk filter.</div>';
    }

    async function loadAdmin() {

        try {

            if (
                !(await checkAdminAuth())
            ) {

                return;
            }


            const d =
                await api(
                    '/api/admin/dashboard'
                );


            const s =
                d.stats;


            $('#adminStats').innerHTML =
                [
                    [
                        'Total Establishments',
                        s.total_establishments
                    ],

                    [
                        'Verified Reports',
                        s.verified_reports
                    ],

                    [
                        'Pending Complaints',
                        s.pending_complaints
                    ],

                    [
                        'High Risk',
                        s.high_risk
                    ],

                    [
                        'Expiring Inventory',
                        s.expiring_inventory
                    ],

                    [
                        'Expired Inventory',
                        s.expired_inventory
                    ],

                    [
                        'Verified Visits',
                        s.verified_visits
                    ]

                ]
                .map(
                    x =>
                        `
                        <div class="stat">

                            <span>
                                ${x[0]}
                            </span>

                            <b>
                                ${x[1]}
                            </b>

                        </div>
                        `
                )
                .join('');


            const is=d.inventory_summary||{};
            $('#adminOverview').innerHTML=[['📦','Inventory Items',is.total_items||0],['🟢','Safe Stock',is.safe||0],['🟡','Low Stock',is.low_stock||0],['⏳','Near Expiry',is.expiring||0],['🔴','Expired',is.expired||0],['⚠️','Safety Incidents',is.incidents||0]].map(x=>`<div class="admin-mini"><span>${x[0]}</span><small>${x[1]}</small><b>${x[2]}</b></div>`).join('');
            const total=Math.max(1,Number(is.total_items||0)); const safePct=Math.round((Number(is.safe||0)/total)*100);
            const riskRows=(d.risk_overview||[]); const riskCounts=riskRows.reduce((a,r)=>(a[r.risk.level]=(a[r.risk.level]||0)+1,a),{});
            $('#adminOverviewDetails').innerHTML=`<div class="overview-health"><div><small>INVENTORY HEALTH</small><b>${safePct}% Safe Stock</b><div class="health-track"><span style="width:${safePct}%"></span></div></div><div class="overview-mini"><span>🟢</span><b>${riskCounts.SAFE||0}</b><small>Safe Restaurants</small></div><div class="overview-mini"><span>🟡</span><b>${riskCounts.MEDIUM||0}</b><small>Medium Risk</small></div><div class="overview-mini"><span>🔴</span><b>${riskCounts.HIGH||0}</b><small>High Risk</small></div></div>`;
            window.__riskOverview = d.risk_overview||[]; renderRiskOverview('ALL');

            const pcs=d.priority_complaints||[]; const pCount=pcs.reduce((a,c)=>(a[c.priority]=(a[c.priority]||0)+1,a),{});
            $('#prioritySummary').innerHTML=[['🚨','Critical / High', (pCount.HIGH||0)+(pCount.CRITICAL||0)],['🟠','Medium',pCount.MEDIUM||0],['🧾','Open Cases',pcs.length],['⭐','Top Score',pcs.length?Math.round(pcs[0].priority_score||0):0]].map(x=>`<div class="priority-kpi"><span>${x[0]}</span><small>${x[1]}</small><b>${x[2]}</b></div>`).join('');

            $('#priorityComplaints').innerHTML =
                d.priority_complaints
                    .map(
                        c =>
                            `
                            <div class="case priority-case">

                                <div class="row">

                                    <b>

                                        ${esc(c.restaurant)}

                                        ·

                                        ${esc(c.category)}

                                    </b>


                                    <span
                                        class="badge ${c.priority.toLowerCase()}"
                                    >
                                        ${esc(c.priority)}
                                    </span>

                                </div>


                                <div class="meta">

                                    Severity
                                    ${c.severity}/10

                                    · Score
                                    ${Math.round(
                                        c.priority_score
                                    )}

                                    ·

                                    ${esc(
                                        c.verification_status
                                    )}

                                </div>


                                <div class="small">${esc(c.description)}</div><div class="priority-meta"><span>Priority score <b>${Math.round(c.priority_score||0)}</b></span><span>Severity <b>${c.severity}/10</b></span><span>Status <b>${esc(c.verification_status||"PENDING")}</b></span></div>


                                ${
                                    c.verification_status ===
                                    'PENDING'

                                        ? `
                                        <div
                                            class="row"
                                            style="margin-top:10px"
                                        >

                                            <button
                                                onclick="
                                                    reviewComplaint(
                                                        '${esc(c.id)}',
                                                        'VERIFY'
                                                    )
                                                "
                                            >
                                                Verify
                                            </button>


                                            <button
                                                onclick="
                                                    reviewComplaint(
                                                        '${esc(c.id)}',
                                                        'REJECT'
                                                    )
                                                "
                                            >
                                                Reject
                                            </button>

                                        </div>
                                        `

                                        : ''
                                }

                            </div>
                            `
                    )
                    .join('')

                ||
                `
                <div class="notice">
                    No complaints.
                </div>
                `;


            const alerts=(d.inventory_alerts||[]);
            const renderExpiry=(mode='NEAR')=>{
                const filtered=alerts.filter(x=>mode==='EXPIRED'?x.status==='EXPIRED':mode==='LOW'?x.status==='LOW STOCK':x.status==='EXPIRING SOON');
                const title=mode==='EXPIRED'?'Expired Items':mode==='LOW'?'Low Stock Alerts':'Near-Expiry Alerts';
                $('#expiryPanelTitle').textContent=title;
                $('#adminAlerts').innerHTML=filtered.map(x=>`<div class="inv alert-card ${String(x.status).toLowerCase().replaceAll(' ','-')}"><div class="row"><b>${esc(x.icon||'🍽️')} ${esc(x.product)}</b><span class="badge ${String(x.status).toLowerCase().replaceAll(' ','-')}">${esc(x.status)}</span></div><div class="meta"><b>${esc(x.restaurant||'Restaurant')}</b> · ${esc(x.category||'Other')} · ${esc(x.quantity)} ${esc(x.unit||'')} · Batch ${esc(x.batch_number||'—')}</div><div class="small">${x.status==='EXPIRED'?'🔴 '+Math.abs(x.days_remaining||0)+' day(s) overdue':x.status==='EXPIRING SOON'?'🟠 '+Math.max(0,x.days_remaining||0)+' day(s) left — action recommended':'🟡 Reorder threshold reached'} · Expiry ${esc(x.expiry_date)} · Storage ${esc(x.storage_condition||'Ambient')}</div><div class="alert-actions"><span>Supplier: ${esc(x.supplier||'—')}</span><span>Reorder: ${esc(x.reorder_level||'—')} ${esc(x.unit||'')}</span></div></div>`).join('')||'<div class="notice">No items in this alert category.</div>';
            };
            $('#expirySummary').innerHTML=[['⏳','Near Expiry',alerts.filter(x=>x.status==='EXPIRING SOON').length],['🔴','Expired',alerts.filter(x=>x.status==='EXPIRED').length],['🟡','Low Stock',alerts.filter(x=>x.status==='LOW STOCK').length]].map(x=>`<div class="expiry-kpi"><span>${x[0]}</span><small>${x[1]}</small><b>${x[2]}</b></div>`).join('');
            $('#expiryFilters')?.addEventListener('click',e=>{const b=e.target.closest('[data-expiry-filter]');if(!b)return;$$('#expiryFilters button').forEach(x=>x.classList.toggle('active',x===b));renderExpiry(b.dataset.expiryFilter)});
            renderExpiry('NEAR');



            notifyIfNeeded(
                d.stats
            );


        } catch (e) {

            $('#priorityComplaints').innerHTML =
                `
                <div class="notice error">

                    Admin dashboard unavailable:

                    ${esc(e.message)}

                </div>
                `;
        }
    }


    // =========================================================
    // =========================================================
    // ADMIN DETAILS / ANALYTICS
    // =========================================================
    function lineGraph(rows, valueKey, title, subtitle, labelKey='name', valueLabel='Score') {
        const W=1000,H=340,pad={l:58,r:28,t:46,b:82};
        const innerW=W-pad.l-pad.r, innerH=H-pad.t-pad.b;
        const pts=rows.map((r,i)=>{const x=pad.l+(rows.length<=1?innerW/2:i*innerW/(rows.length-1));const v=Math.max(0,Math.min(100,Number(r[valueKey])||0));const y=pad.t+innerH-v/100*innerH;return {x,y,v,r};});
        const grid=[0,25,50,75,100].map(v=>{const y=pad.t+innerH-v/100*innerH;return `<line x1="${pad.l}" y1="${y}" x2="${W-pad.r}" y2="${y}" class="chart-grid"/><text x="${pad.l-10}" y="${y+4}" text-anchor="end" class="chart-axis">${v}</text>`}).join('');
        const poly=pts.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
        const labels=pts.map(p=>{const raw=String(p.r[labelKey]||'');const label=raw.length>16?raw.slice(0,14)+'…':raw;return `<text x="${p.x}" y="${H-47}" text-anchor="end" transform="rotate(-42 ${p.x} ${H-47})" class="chart-label">${esc(label)}</text>`}).join('');
        const circles=pts.map(p=>`<circle cx="${p.x}" cy="${p.y}" r="5" class="chart-point"><title>${esc(p.r[labelKey])}: ${Math.round(p.v)}/100</title></circle>`).join('');
        return `<div class="graph-card"><div class="graph-card-head"><div><b>${esc(title)}</b><span>${esc(subtitle)}</span></div><strong>0–100</strong></div><div class="line-chart-wrap"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)}">${grid}<polyline points="${poly}" class="chart-line"/>${circles}${labels}</svg></div><div class="chart-axis-caption">${esc(valueLabel)}</div></div>`;
    }

    function factorLineGraph(rows, title, subtitle) {
        return lineGraph(rows,'score',title,subtitle,'name','Factor score');
    }

    function populateDetailsRestaurants(rows) {
        const options=rows.map(r=>`<option value="${r.id}">${esc(r.name)}</option>`).join('');
        ['#riskFactorRestaurant','#inventoryGraphRestaurant'].forEach(sel=>{const el=$(sel);if(el)el.innerHTML=options;});
    }

    async function loadAdminDetails() {
        try {
            if (!(await checkAdminAuth())) return;
            const d=await api('/api/admin/details');
            const rows=d.restaurants||[];
            populateDetailsRestaurants(rows);
            showDetailsChoice();
        } catch(e) {
            const choice=$('#detailsChoicePanel');
            if(choice) choice.innerHTML=`<div class="notice error">Unable to load details: ${esc(e.message)}</div>`;
        }
    }

    function showDetailsChoice() {
        $('#detailsChoicePanel')?.classList.remove('hidden');
        ['#detailsOverallPanel','#detailsRiskPanel','#detailsInventoryPanel'].forEach(sel=>$(sel)?.classList.add('hidden'));
    }

    async function openDetailsMode(mode) {
        $('#detailsChoicePanel')?.classList.add('hidden');
        ['#detailsOverallPanel','#detailsRiskPanel','#detailsInventoryPanel'].forEach(sel=>$(sel)?.classList.add('hidden'));
        if(mode==='overall') {
            $('#detailsOverallPanel')?.classList.remove('hidden');
            try {
                const d=await api('/api/admin/details');
                const rows=d.restaurants||[];
                $('#overallRiskGraph').innerHTML=rows.length?lineGraph(rows,'risk_score','Overall FoodSafe Risk Score','All restaurants — higher score indicates a stronger safety indicator','name','Risk score'): '<div class="notice">No restaurant data available.</div>';
            } catch(e) { $('#overallRiskGraph').innerHTML=`<div class="notice error">${esc(e.message)}</div>`; }
        } else if(mode==='risk') {
            $('#detailsRiskPanel')?.classList.remove('hidden');
            if($('#riskFactorRestaurant')?.value) await renderRiskFactorDetails();
        } else if(mode==='inventory') {
            $('#detailsInventoryPanel')?.classList.remove('hidden');
            if($('#inventoryGraphRestaurant')?.value) await renderInventoryGraphDetails();
        }
    }

    document.querySelectorAll('[data-detail-mode]').forEach(btn=>btn.addEventListener('click',()=>openDetailsMode(btn.dataset.detailMode)));
    document.querySelectorAll('[data-details-back]').forEach(btn=>btn.addEventListener('click',showDetailsChoice));

    async function renderRiskFactorDetails() {
        const rid=$('#riskFactorRestaurant')?.value;
        if(!rid)return;
        try {
            const d=await api('/api/admin/details/risk/'+encodeURIComponent(rid));
            const factors=d.factors||[];
            $('#riskFactorFormula').innerHTML=`<b>Final Risk Score: ${Math.round(d.risk_score)}/100</b><span>Weighted factor composite · Higher = safer indicator</span><span class="notice">${esc(d.data_status || 'SIMULATED DEMO DATA — NOT AN OFFICIAL INSPECTION RECORD')}</span>`;
            const graphHtml=factors.length?factorLineGraph(factors,`${d.name} — Risk Factors`,`Cumulative weighted score after each factor`):'<div class="notice">No risk factors available.</div>';
            const rowsHtml=factors.filter(f=>f.name!=='Starting score').map(f=>`<tr><td>${esc(f.name)}</td><td>${esc(f.value ?? '—')}</td><td>${esc(f.category ?? '—')}</td><td>${Number(f.points)>0?'+':''}${Number(f.points||0)}</td><td>${Number(f.score||0)}/100</td></tr>`).join('');
            $('#riskFactorGraph').innerHTML=graphHtml+(rowsHtml?`<div class="table-wrap risk-factor-table-wrap"><table class="data-table"><thead><tr><th>Factor</th><th>Recorded value</th><th>Category</th><th>Weighted points</th><th>Score after factor</th></tr></thead><tbody>${rowsHtml}</tbody></table></div>`:'')+`<p class="muted">${esc(d.explanation || 'Scores are prototype indicators generated from the seeded compliance factors.')}</p>`;
        }catch(e){$('#riskFactorGraph').innerHTML=`<div class="notice error">${esc(e.message)}</div>`;}
    }

    async function renderInventoryGraphDetails() {
        const rid=$('#inventoryGraphRestaurant')?.value;
        if(!rid)return;
        try {
            const d=await api('/api/admin/details/inventory/'+encodeURIComponent(rid));
            const items=d.items||[];
            $('#inventoryGraphMeta').innerHTML=`<span><b>${esc(d.name)}</b></span><span>${items.length} stock item(s)</span><span>Higher score = healthier item</span>`;
            $('#inventoryGraph').innerHTML=items.length?lineGraph(items,'health_score',`${d.name} — Inventory Health`,`Health score for each inventory item`,'product','Inventory health'): '<div class="notice">No inventory items available for this restaurant.</div>';
        }catch(e){$('#inventoryGraph').innerHTML=`<div class="notice error">${esc(e.message)}</div>`;}
    }

    $('#riskFactorRestaurant')?.addEventListener('change',renderRiskFactorDetails);
    $('#inventoryGraphRestaurant')?.addEventListener('change',renderInventoryGraphDetails);

    // NOTIFICATIONS
    // =========================================================

    function alertsEnabled() {
        return localStorage.getItem('foodsafeAlertsEnabled') === '1';
    }

    function syncAlertButton() {
        const b = $('#notifyButton');
        if (!b) return;

        if (!('Notification' in window)) {
            b.textContent = 'Alerts Unsupported';
            b.disabled = true;
            return;
        }

        if (Notification.permission === 'denied') {
            b.textContent = 'Alerts Blocked';
            return;
        }

        b.textContent = alertsEnabled() ? 'Disable Alerts' : 'Enable Alerts';
    }

    function notifyIfNeeded(s) {

        if (
            !alertsEnabled()
            ||
            !('Notification' in window)
            ||
            Notification.permission !==
            'granted'
        ) {

            return;
        }


        if (
            s.expired_inventory > 0
        ) {

            new Notification(
                'FoodSafe Alert',
                {
                    body:
                        `${s.expired_inventory} expired inventory item(s) need attention.`
                }
            );
        }
    }


    $('#notifyButton')
        .addEventListener(
            'click',
            async () => {

                if (!('Notification' in window)) {
                    alert('Browser notifications are not supported.');
                    return;
                }

                if (alertsEnabled()) {
                    localStorage.setItem('foodsafeAlertsEnabled', '0');
                    syncAlertButton();
                    return;
                }

                let p = Notification.permission;
                if (p !== 'granted') {
                    p = await Notification.requestPermission();
                }

                if (p === 'granted') {
                    localStorage.setItem('foodsafeAlertsEnabled', '1');
                }

                syncAlertButton();
            }
        );

    syncAlertButton();


    // =========================================================
    // VERIFIED VISIT
    // =========================================================

    $('#visitTimestamp').value =
        nowLocal();


    // =========================================================
    // BROWSER GPS
    // =========================================================

    function getBrowserLocation() {

        return new Promise(
            (
                resolve,
                reject
            ) => {

                if (
                    !navigator.geolocation
                ) {

                    reject(
                        new Error(
                            'Geolocation is not supported by this browser.'
                        )
                    );

                    return;
                }


                navigator.geolocation
                    .getCurrentPosition(

                        position => {

                            resolve({

                                latitude:
                                    position.coords.latitude,

                                longitude:
                                    position.coords.longitude,

                                accuracy:
                                    position.coords.accuracy

                            });
                        },


                        error => {

                            let message =
                                'Unable to get your location.';


                            switch (
                                error.code
                            ) {

                                case error.PERMISSION_DENIED:

                                    message =
                                        'Location permission was denied. Please allow location access.';

                                    break;


                                case error.POSITION_UNAVAILABLE:

                                    message =
                                        'Your location is currently unavailable.';

                                    break;


                                case error.TIMEOUT:

                                    message =
                                        'Location request timed out. Try again.';

                                    break;
                            }


                            reject(
                                new Error(
                                    message
                                )
                            );
                        },


                        {
                            enableHighAccuracy:
                                true,

                            timeout:
                                15000,

                            maximumAge:
                                0
                        }
                    );
            }
        );
    }


    async function captureLocation() {

        const button =
            $('#getLocationButton');

        const status =
            $('#locationStatus');


        button.disabled = true;

        button.textContent =
            'Getting Location...';


        status.className =
            'small';


        status.textContent =
            'Requesting your browser GPS location...';


        try {

            const location =
                await getBrowserLocation();


            $('#visitLatitude').value =
                location.latitude;


            $('#visitLongitude').value =
                location.longitude;


            $('#latitudeDisplay').textContent =
                location.latitude.toFixed(6);


            $('#longitudeDisplay').textContent =
                location.longitude.toFixed(6);


            $('#distanceDisplay').textContent =
                'Will be calculated by server';


            $('#visitLocation').value =
                `${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}`;


            status.className =
                'small success';


            status.innerHTML =
                `
                ✓ Location captured.

                GPS accuracy:
                ${Math.round(
                    location.accuracy
                )} m.

                The server will verify your
                distance from the selected restaurant.
                `;


            $('#locationVerified')
                .checked = true;

        } catch (error) {

            status.className =
                'small error';


            status.textContent =
                error.message;


            $('#visitLatitude').value =
                '';

            $('#visitLongitude').value =
                '';

        } finally {

            button.disabled = false;

            button.textContent =
                'Get My Location';
        }
    }


    $('#getLocationButton')
        ?.addEventListener(
            'click',
            captureLocation
        );


    // =========================================================
    // LOCATION CHECKBOX
    // =========================================================

    $('#locationVerified')
        ?.addEventListener(
            'change',
            e => {

                if (
                    e.target.checked
                    &&
                    !$('#visitLatitude').value
                ) {

                    $('#locationStatus')
                        .textContent =
                        'Click "Get My Location" to capture GPS coordinates.';
                }
            }
        );


    // =========================================================
    // VERIFIED VISIT SUBMISSION
    // =========================================================

    $('#visitForm')
        .addEventListener(
            'submit',
            async e => {

                e.preventDefault();


                const button =
                    e.submitter;


                button.disabled = true;


                try {

                    const locationRequired =
                        $('#locationVerified')
                            .checked;


                    // -------------------------------------------------
                    // Capture GPS automatically if Location is selected.
                    // -------------------------------------------------

                    if (
                        locationRequired
                        &&
                        (
                            !$('#visitLatitude').value
                            ||
                            !$('#visitLongitude').value
                        )
                    ) {

                        await captureLocation();
                    }


                    // -------------------------------------------------
                    // Verify that GPS was captured.
                    // -------------------------------------------------

                    if (
                        locationRequired
                        &&
                        (
                            !$('#visitLatitude').value
                            ||
                            !$('#visitLongitude').value
                        )
                    ) {

                        throw new Error(
                            'Location verification requires your GPS position. Click "Get My Location" and allow browser location access.'
                        );
                    }


                    const fd =
                        new FormData(
                            e.target
                        );


                    // -------------------------------------------------
                    // Checkbox values.
                    // -------------------------------------------------

                    [
                        'qr',
                        'location_verified',
                        'timestamp_verified',
                        'bill',
                        'otp'
                    ].forEach(
                        name => {

                            fd.set(
                                name,

                                $(
                                    `input[name="${name}"]`
                                ).checked
                                    ? '1'
                                    : '0'
                            );
                        }
                    );


                    // -------------------------------------------------
                    // Location text.
                    // -------------------------------------------------

                    fd.set(
                        'location',
                        $('#visitLocation')
                            .value
                    );


                    // -------------------------------------------------
                    // SEND TO BACKEND
                    // -------------------------------------------------

                    const r =
                        await api(
                            '/api/visits',
                            {
                                method: 'POST',

                                body: fd
                            }
                        );


                    // -------------------------------------------------
                    // DISTANCE
                    // -------------------------------------------------

                    const distance =
                        r.distance_meters != null

                            ? `
                                <br>
                                Distance:
                                <strong>
                                    ${r.distance_meters} m
                                </strong>
                              `

                            : '';


                    // -------------------------------------------------
                    // RESULT
                    // -------------------------------------------------

                    $('#visitResult').innerHTML =
                        `
                        <div class="notice success">

                            <b>
                                ✓
                                ${esc(
                                    r.verification_status
                                )}
                            </b>

                            <br>

                            Visit ID:

                            <strong>
                                ${esc(r.id)}
                            </strong>

                            <br>

                            Verification Score:

                            <strong>
                                ${r.verification_score}/100
                            </strong>

                            ${distance}

                            <br>

                            Evidence:

                            ${r.methods
                                .map(esc)
                                .join(', ')}

                        </div>
                        `;


                    loadVisits();

                } catch (x) {

                    $('#visitResult').innerHTML =
                        `
                        <div class="notice error">
                            ${esc(x.message)}
                        </div>
                        `;

                } finally {

                    button.disabled = false;
                }
            }
        );


    // =========================================================
    // VERIFIED VISIT HISTORY
    // =========================================================

    async function loadVisits() {

        try {

            const d =
                await api(
                    '/api/visits'
                );


            $('#visitsList').innerHTML =
                d
                    .slice(0, 8)
                    .map(
                        v =>
                            `
                            <div class="case">

                                <b>
                                    ${esc(
                                        v.restaurant
                                    )}
                                </b>


                                <div class="meta">

                                    ${esc(
                                        v.verification_status
                                    )}

                                    ·

                                    ${esc(v.methods)}

                                    · Score
                                    ${v.verification_score}

                                    ·

                                    ${esc(v.timestamp)}

                                </div>


                                ${
                                    v.distance_meters != null

                                        ? `
                                            <div class="small">

                                                GPS Distance:

                                                ${Number(
                                                    v.distance_meters
                                                ).toFixed(2)}

                                                m

                                            </div>
                                          `

                                        : ''
                                }

                            </div>
                            `
                    )
                    .join('')

                ||
                `
                <div class="notice">
                    No verified visits yet.
                </div>
                `;

        } catch (e) {

            $('#visitsList').innerHTML =
                `
                <div class="notice error">
                    Unable to load visits.
                </div>
                `;
        }
    }


    // =========================================================
    // QR GENERATION
    // =========================================================

    $('#generateQr')
        .addEventListener(
            'click',
            async () => {

                try {

                    const id =
                        $('#qrRestaurant')
                            .value;


                    const r =
                        await fetch(
                            `/api/restaurants/${id}/qr`
                        );


                    if (!r.ok) {

                        throw Error(
                            'QR generation unavailable'
                        );
                    }


                    const blob =
                        await r.blob();


                    $('#qrImage').src =
                        URL.createObjectURL(
                            blob
                        );


                    $('#qrImage')
                        .classList
                        .remove('hidden');

                } catch (e) {

                    $('#otpResult').innerHTML =
                        `
                        <div class="notice error">

                            ${esc(e.message)}.

                            Install qrcode from
                            requirements.txt.

                        </div>
                        `;
                }
            }
        );


    // =========================================================
    // REAL SMS OTP
    // =========================================================

    $('#sendOtp').addEventListener('click', async e => {
        e.preventDefault();
        const out = $('#otpResult');
        const button = $('#sendOtp');
        const phone = $('#otpPhone').value.trim();
        if (!phone) {
            out.innerHTML = '<div class="notice error">Enter the mobile number that should receive the SMS.</div>';
            $('#otpPhone').focus();
            return;
        }
        button.disabled = true;
        button.textContent = 'Sending SMS…';
        try {
            const d = await api('/api/visits/otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone })
            });
            $('#visitOtpPhone').value = d.phone || phone;
            const otpInput = $('#visitForm input[name="otp_code"]');
            if (otpInput) otpInput.value = '';
            const otpCheck = $('#visitForm input[name="otp"]');
            if (otpCheck) otpCheck.checked = true;
            out.innerHTML = `<div class="notice success">${esc(d.message || 'SMS OTP sent. Check your messages and enter the code in the Verified Visit form.')}</div>`;
        } catch (err) {
            out.innerHTML = `<div class="notice error">SMS could not be sent: ${esc(err.message)}. Check the mobile number and Twilio configuration in Food_Safe/.env.</div>`;
        } finally {
            button.disabled = false;
            button.textContent = 'Send SMS OTP';
        }
    });

    // =========================================================
    // FREE DEMO OTP (separate from real SMS OTP)
    // =========================================================

    $('#generateDemoOtp').addEventListener('click', async e => {
        e.preventDefault();
        const out = $('#demoOtpResult');
        const button = $('#generateDemoOtp');
        const phone = $('#otpPhone').value.trim();
        if (!phone) {
            out.innerHTML = '<div class="notice error">Enter a mobile number above to associate it with this demo verification.</div>';
            $('#otpPhone').focus();
            return;
        }
        button.disabled = true;
        button.textContent = 'Generating…';
        try {
            const d = await api('/api/visits/demo-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone })
            });
            $('#visitOtpPhone').value = d.phone || phone;
            const otpInput = $('#visitForm input[name="otp_code"]');
            if (otpInput) otpInput.value = '';
            const otpCheck = $('#visitForm input[name="otp"]');
            if (otpCheck) otpCheck.checked = true;
            out.innerHTML = `<div class="notice success"><strong>Demo OTP: <span style="font-size:1.2em;letter-spacing:.12em">${esc(d.demo_code)}</span></strong><br>${esc(d.message || 'Enter this code in the Verified Visit form.')}<br><small>Demo only — not sent by SMS.</small></div>`;
        } catch (err) {
            out.innerHTML = `<div class="notice error">Could not generate demo OTP: ${esc(err.message)}</div>`;
        } finally {
            button.disabled = false;
            button.textContent = 'Generate Demo OTP';
        }
    });

    // =========================================================
    // QR SCANNER
    // =========================================================

    async function startQr() {

        const box =
            $('#qrReader');

        const video =
            $('#qrVideo');


        if (
            !('BarcodeDetector' in window)
        ) {

            box.classList.remove(
                'hidden'
            );


            $('#qrStatus').textContent =
                'This browser does not expose BarcodeDetector. Generate a QR and use Search as the fallback.';

            return;
        }


        try {

            qrStream =
                await navigator
                    .mediaDevices
                    .getUserMedia({
                        video: {
                            facingMode:
                                'environment'
                        }
                    });


            video.srcObject =
                qrStream;


            box.classList.remove(
                'hidden'
            );


            const detector =
                new BarcodeDetector({
                    formats: [
                        'qr_code'
                    ]
                });


            const loop =
                async () => {

                    if (!qrStream) {
                        return;
                    }


                    try {

                        const codes =
                            await detector.detect(
                                video
                            );


                        if (
                            codes[0]?.rawValue
                        ) {

                            const u =
                                new URL(
                                    codes[0].rawValue
                                );


                            const id =
                                u.searchParams
                                    .get(
                                        'restaurant'
                                    );


                            if (id) {

                                stopQr();

                                profile(
                                    Number(id)
                                );

                                return;
                            }
                        }

                    } catch {}


                    scanTimer =
                        requestAnimationFrame(
                            loop
                        );
                };


            loop();

        } catch (e) {

            box.classList.remove(
                'hidden'
            );


            $('#qrStatus').textContent =
                'Camera access failed. Allow camera permission or use Search.';
        }
    }


    function stopQr() {

        if (scanTimer) {

            cancelAnimationFrame(
                scanTimer
            );
        }


        scanTimer = null;


        if (qrStream) {

            qrStream
                .getTracks()
                .forEach(
                    t => t.stop()
                );
        }


        qrStream = null;


        $('#qrReader')
            .classList
            .add('hidden');
    }


    $('#scanQrButton')
        .addEventListener(
            'click',
            startQr
        );


    $('#closeQr')
        .addEventListener(
            'click',
            stopQr
        );
        // =========================================================
// QR GENERATION
// =========================================================

$('#generateQr')
    .addEventListener(
        'click',
        async () => {

            try {

                const id =
                    $('#qrRestaurant')
                        .value;


                const r =
                    await fetch(
                        `/api/restaurants/${id}/qr`
                    );


                if (!r.ok) {

                    throw Error(
                        'QR generation unavailable'
                    );
                }


                const blob =
                    await r.blob();


                $('#qrImage').src =
                    URL.createObjectURL(
                        blob
                    );


                $('#qrImage')
                    .classList
                    .remove('hidden');

            } catch (e) {

                $('#qrStatus').innerHTML =
                    `
                    <div class="notice error">

                        ${esc(e.message)}.

                        Install qrcode from
                        requirements.txt.

                    </div>
                    `;
            }
        }
    );


    // =========================================================
    // OCR
    // =========================================================

    const ocrInput = $('#ocrFile');
    const photoPreview = $('#photoSelectionPreview');
    let selectedPhotoUrl = null;
    ocrInput?.addEventListener('change', () => {
        const f = ocrInput.files?.[0];
        if (selectedPhotoUrl) URL.revokeObjectURL(selectedPhotoUrl);
        selectedPhotoUrl = null;
        if (!f) { photoPreview?.classList.add('hidden'); photoPreview.innerHTML=''; return; }
        if (!f.type.startsWith('image/')) { photoPreview?.classList.remove('hidden'); photoPreview.innerHTML='<div class="notice error">Please choose an image file.</div>'; return; }
        selectedPhotoUrl = URL.createObjectURL(f);
        photoPreview.classList.remove('hidden');
        photoPreview.innerHTML = `<div class="photo-selected-card"><img src="${selectedPhotoUrl}" alt="Selected restaurant photo preview"><div><b>✓ Photo selected</b><div>${esc(f.name)}</div><small>${(f.size/1024).toFixed(0)} KB · Ready to identify</small><button type="button" class="secondary" id="clearSelectedPhoto">× Remove photo</button></div></div>`;
    });
    photoPreview?.addEventListener('click', e => { if(e.target.closest('#clearSelectedPhoto')) { ocrInput.value=''; photoPreview.classList.add('hidden'); photoPreview.innerHTML=''; if(selectedPhotoUrl)URL.revokeObjectURL(selectedPhotoUrl); selectedPhotoUrl=null; $('#ocrResult').innerHTML=''; } });

    $('#ocrButton')?.addEventListener('click', async () => {
        const f = ocrInput?.files?.[0];
        if (!f) { $('#ocrResult').innerHTML='<div class="notice error">Choose a photo first. The selected photo will appear above this button.</div>'; return; }
        if (f.size > 10 * 1024 * 1024) { $('#ocrResult').innerHTML='<div class="notice error">Photo is too large. Choose an image under 10 MB.</div>'; return; }
        const fd = new FormData(); fd.append('image', f);
        $('#ocrResult').innerHTML='<div class="notice">🔎 Reading sign/menu text and matching restaurant names…</div>';
        try {
            const d = await api('/api/ocr', {method:'POST',body:fd});
            const photoMatches = d.matches || d.restaurants || (d.restaurant ? [d.restaurant] : []);
            const exact = photoMatches.some(x => Number(x.match_score||0) >= 78);
            $('#ocrResult').innerHTML = `<div class="notice ${photoMatches.length?'success':''}"><b>OCR result:</b><p>${esc(d.text || 'No readable text detected')}</p>${photoMatches.length ? `<b>${exact?'Likely match':'Suggested restaurants — select the correct one'}:</b><div class="ocr-suggestions">${photoMatches.map((r,i)=>`<button type="button" class="ocr-suggestion" data-profile="${Number(r.id)}"><img class="ocr-suggestion-image" src="${esc(r.image_url || `/images/restaurants/fallback-${Number(r.id)}.svg`)}" alt="Illustrative image for ${esc(r.name)}" onerror="this.onerror=null;this.src='/images/restaurants/fallback-${Number(r.id)}.svg'"><b>${esc(r.name)}</b><small>${esc(r.area||'')} · Match ${esc(r.match_score ?? '—')}%</small></button>`).join('')}</div>` : '<p>No text could be matched. Try a closer, brighter photo of the restaurant name/sign or menu, or search by name.</p>'}</div>`;
        } catch(e) { $('#ocrResult').innerHTML=`<div class="notice error">${esc(e.message)}<br><small>Check that Tesseract OCR is installed and available, then restart FoodSafe.</small></div>`; }
    });

    $('#ocrResult')
        .addEventListener(
            'click',
            e => {

                const b =
                    e.target.closest(
                        '[data-profile]'
                    );


                if (b) {

                    profile(
                        Number(
                            b.dataset.profile
                        )
                    );
                }
            }
        );


    syncPrivateAccess();

    // =========================================================
    // INITIAL LOAD
    // =========================================================

    // Consumer restaurant list is intentionally hidden on initial load.
    // Restaurants are loaded when the user searches or clicks Show Restaurants.
    // Load map directory on startup; the main restaurant results remain hidden until requested.
    api('/api/restaurants').then(data => {
        if (Array.isArray(data)) updateRestaurantMap(data, true);
    }).catch(() => {
        const map = $('#restaurantMap');
        const list = $('#restaurantMapList');
        if (map) map.innerHTML = '<div class="map-fallback"><strong>Restaurant data could not be loaded.</strong><p>Check that the FoodSafe backend is running, then refresh.</p></div>';
        if (list) list.innerHTML = '<p class="map-empty">Could not load restaurants. Refresh after starting the backend.</p>';
    });

    const initialId = new URLSearchParams(location.search).get('restaurant');
    if (initialId && Number(initialId)) {
        profile(Number(initialId));
    }

})();