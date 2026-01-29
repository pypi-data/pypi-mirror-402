/* global ol */
'use strict';

class WMTSWidget extends MapWidget {

    /**
     * Overrides MapWiget.createMap() that is called by
     * MapWidget itself and stores the map in this.map
     * @returns ol.Map instance
     */
    createMap() {
        this.map_extent = this.options.extent;
        this.projection = new ol.proj.Projection({
            code: `EPSG:${this.options.map_srid}`,
            extent: this.map_extent,
        });
        return new ol.Map({
            target: this.options.map_id,
            layers: [this.options.base_layer],
            view: new ol.View({
                center: this.options.default_center,
                resolution: this.options.default_resolution,
                projection: this.projection,
                resolutions: this.options.resolutions,
                constrainResolution: true
            })
        });
    }

    defaultCenter() {
        return this.options.default_center;
    }

    search(searchterm) {
        let debounceTimeout;
        const query = searchterm.trim();
    
        clearTimeout(debounceTimeout);
        if (query.length < 3) {
            this.clearResults()
            return;
        }
    
        debounceTimeout = setTimeout(() => {
        const url = this.options.search_url.replace('{search_term}', encodeURIComponent(query));
    
        fetch(url)
            .then(response => response.json())
            .then(data => {
            this.clearResults();
            if (data && data.features) {
                data.features.forEach(feature => {
                    const label = feature.properties.label;
                    const coords = feature.geometry.coordinates;
                    const div = document.createElement("div");
                    div.textContent = label;
                    div.addEventListener("click", () => {
                        this.clearResults();
                        this.inputSearchElement.value = label;
                        this.map.getView().fit(feature.bbox, {padding: [50, 50, 50, 50]})
                    });
                    this.divSearchResults.appendChild(div);
                    this.divSearchResults.classList.remove("ext-ol-hidden");
                });
            }
            })
            .catch(error => {
                console.error("Search error!", error);
                console.error(`Something went wrong parsing the response of ${url}`);
            });
        }, 300);
    }

    clearResults() {
        this.divSearchResults.innerHTML = "";
        this.divSearchResults.classList.add("ext-ol-hidden");
    }

    createInteractions() {
        super.createInteractions();
        document.addEventListener("DOMContentLoaded", () => {
            document.querySelectorAll('.ext-ol-search-widget').forEach((divElement) => {
                this.inputSearchElement = divElement.querySelector('input');
                this.divSearchResults = divElement.querySelector('div.ext-ol-autocomplete-results');
                this.inputSearchElement.addEventListener("input", () => this.search(this.inputSearchElement.value));
            });
        });
        this.featureOverlay.setStyle(vectorLayerStyle);
    }
}


