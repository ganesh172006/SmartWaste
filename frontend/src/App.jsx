import { useEffect, useMemo, useState } from "react";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet";

import L from "leaflet";

import "leaflet/dist/leaflet.css";



// API base URL:
// Set VITE_API_URL in Render for production; this URL is the fallback.
const API = (
  import.meta.env.VITE_API_URL ||
  "https://smartwaste-api-f46n.onrender.com"
).replace(/\/+$/, "");


const DEPOT = [
  12.9716,
  77.5946,
];


const ROUTE_COLORS = [
  "#2563eb",
  "#16a34a",
  "#7c3aed",
  "#ea580c",
];


// =====================================================
// PRIORITY COLOR
// =====================================================

function getPriorityColor(priority) {

  switch (priority) {

    case "CRITICAL":
      return "#dc2626";

    case "HIGH":
      return "#ea580c";

    case "MEDIUM":
      return "#ca8a04";

    case "LOW":
      return "#16a34a";

    default:
      return "#64748b";
  }
}


// =====================================================
// BIN ICON
// =====================================================

function createBinIcon(
  fill,
  priority
) {

  const color =
    getPriorityColor(
      priority
    );


  return L.divIcon({

    className:
      "custom-bin-icon",

    html: `
      <div
        class="bin-marker"
        style="
          --marker-color:${color};
        "
      >
        ${Math.round(fill)}%
      </div>
    `,

    iconSize: [
      48,
      48
    ],

    iconAnchor: [
      24,
      24
    ],

    popupAnchor: [
      0,
      -24
    ],
  });
}


// =====================================================
// DEPOT ICON
// =====================================================

function createDepotIcon() {

  return L.divIcon({

    className:
      "depot-icon",

    html: `
      <div class="depot-marker">
        🚛
      </div>
    `,

    iconSize: [
      50,
      50
    ],

    iconAnchor: [
      25,
      25
    ],
  });
}


// =====================================================
// MAP RESIZE
// =====================================================

function MapResizeHandler() {

  const map = useMap();


  useEffect(() => {

    setTimeout(() => {

      map.invalidateSize();

    }, 300);

  }, [map]);


  return null;
}



const APP_STYLES = `
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#1e2923;background:#f5f8f5;font-synthesis:none;text-rendering:optimizeLegibility}
*{box-sizing:border-box}body{margin:0;background:#f5f8f5}button,input{font:inherit}button{cursor:pointer}
.app{min-height:100vh;color:#202a24}.topbar{height:88px;position:sticky;top:0;z-index:1000;display:flex;align-items:center;justify-content:space-between;padding:14px clamp(18px,4vw,64px);background:rgba(255,255,255,.97);border-bottom:1px solid #e0e7e1;backdrop-filter:blur(12px)}
.brand{display:flex;align-items:center;gap:14px}.brand-logo,.loading-logo{width:58px;height:58px;display:grid;place-items:center;border-radius:18px;background:#20372c;color:#d9f99d;font-size:28px;box-shadow:0 8px 22px #1c33231b}.brand h1{font-size:25px;letter-spacing:-.7px;margin:0 0 2px;font-weight:800}.brand span{font-size:14px;color:#78847c}.topbar-right{display:flex;align-items:center;gap:26px}.system-status,.map-status{display:flex;align-items:center;gap:9px;color:#647168;font-size:14px}.online-dot{width:9px;height:9px;background:#69bd76;display:inline-block;border-radius:50%;box-shadow:0 0 0 5px #69bd761b}.refresh-button,.edit-bin{border:1px solid #dce5dd;background:white;color:#35443a;border-radius:13px;padding:12px 18px;font-weight:700;transition:.2s}.refresh-button:hover,.edit-bin:hover{border-color:#9db9a4;background:#f8fbf8}.dashboard{max-width:1800px;margin:0 auto;padding:28px clamp(16px,2.2vw,40px) 34px}.page-intro{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:28px}.eyebrow{font-size:11px;letter-spacing:1.8px;font-weight:800;color:#64816b;margin:0 0 8px}.page-intro h2{font-size:clamp(28px,3vw,40px);line-height:1.15;letter-spacing:-1.5px;margin:0 0 12px}.intro-text,.panel-header p{margin:0;color:#7c8880;line-height:1.55}.updated-time{display:flex;flex-direction:column;align-items:flex-end;gap:5px;padding-bottom:4px;white-space:nowrap}.updated-time span{font-size:11px;text-transform:uppercase;letter-spacing:1.2px;color:#95a097}.updated-time strong{font-size:15px;color:#526157}.stats-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:14px;margin-bottom:26px}.stat-card,.panel{background:white;border:1px solid #e1e8e2;border-radius:20px;box-shadow:0 3px 14px #1b33200a}.stat-card{padding:21px 22px;min-height:156px}.stat-top{display:flex;align-items:center;justify-content:space-between;color:#78837b;font-size:14px;margin-bottom:18px}.stat-icon{width:38px;height:38px;border-radius:12px;background:#eff5f0;color:#40654c;display:grid;place-items:center;font-weight:800}.stat-card>strong{font-size:35px;letter-spacing:-1.1px;display:block;line-height:1.2}.stat-card>small{display:block;color:#96a098;margin-top:10px;font-size:12px}.stat-card .unit{display:inline!important;font-size:14px;margin-left:4px;color:#829087}.stat-alert{border-color:#f0dada}.stat-alert .stat-icon{background:#fbefef;color:#c94a42}
.main-grid{display:grid;grid-template-columns:minmax(0,1.8fr) minmax(390px,.86fr);gap:22px;align-items:start;margin-bottom:24px}.panel{overflow:hidden;margin-bottom:24px}.panel-header{padding:23px 26px;display:flex;align-items:center;justify-content:space-between;gap:16px;border-bottom:1px solid #edf0ed}.panel-header h3{font-size:20px;letter-spacing:-.4px;margin:0 0 6px}.panel-header p{font-size:13px}.map-container{height:540px;position:relative}.map-container .leaflet-container{height:100%;width:100%;z-index:1}.map-legend{position:absolute;bottom:18px;left:18px;z-index:500;background:#ffffffed;border:1px solid #e2e8e2;border-radius:13px;padding:12px 14px;box-shadow:0 4px 18px #17241c18;display:grid;gap:8px;font-size:12px;color:#526057}.legend-title{font-weight:800;margin-bottom:2px}.legend{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:7px}.legend.critical{background:#dc2626}.legend.high{background:#ea580c}.legend.medium{background:#ca8a04}.legend.normal{background:#16a34a}.bin-marker{width:46px;height:46px;border-radius:50%;display:grid;place-items:center;background:var(--marker-color);color:#fff;border:4px solid #fff;box-shadow:0 4px 14px #14251b45;font-size:14px;font-weight:800}.depot-marker{width:48px;height:48px;border:4px solid white;border-radius:15px;background:#20372c;display:grid;place-items:center;font-size:22px;box-shadow:0 4px 16px #14251b3b}.custom-bin-icon,.depot-icon{background:transparent;border:0}.popup-content{display:grid;gap:7px;min-width:145px}.popup-content>strong{font-size:15px}.popup-content>span,.popup-row span{color:#77847a;font-size:12px}.popup-divider{border-top:1px solid #e8ece8;margin:2px 0}.popup-row{display:flex;justify-content:space-between;gap:15px;font-size:12px}
.bin-panel{min-width:0}.bin-count{min-width:38px;height:38px;display:grid;place-items:center;background:#eff5f0;color:#42654b;border-radius:50%;font-weight:800}.bin-list{padding:0 22px;max-height:560px;overflow:auto}.bin-row{display:grid;grid-template-columns:minmax(100px,1fr) minmax(85px,.7fr) auto;gap:12px;align-items:center;padding:17px 2px;border-bottom:1px solid #edf0ed}.bin-row:last-child{border-bottom:0}.bin-row-main{display:flex;align-items:center;gap:12px;min-width:0}.mini-status{width:9px;height:9px;border-radius:50%;flex-shrink:0}.bin-info{display:flex;flex-direction:column;gap:5px;min-width:0}.bin-info strong{font-size:15px}.bin-info>span:not(.ai-priority-inline){font-size:12px;color:#929b94}.ai-priority-inline{font-size:11px;color:#42694b;font-weight:750;line-height:1.3}.bin-fill{display:flex;flex-direction:column;align-items:flex-end;gap:8px}.bin-fill>strong{font-size:15px}.fill-track{height:6px;width:100%;max-width:110px;border-radius:99px;background:#edf0ed;overflow:hidden}.fill-bar{height:100%;border-radius:99px}.edit-bin{padding:9px 13px;font-size:12px;border-radius:10px}.prediction-mini{grid-column:1/-1;display:flex;gap:8px;margin-left:21px;font-size:11px;color:#89948b}.prediction-mini strong{color:#526e59}.update-box{margin:16px 22px 22px;background:#f8fbf8;border:1px solid #e1e9e2;border-radius:15px;padding:16px}.update-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}.update-header>div{display:grid;gap:4px}.update-header span{font-size:10px;letter-spacing:1.4px;color:#849087}.update-header strong{font-size:16px}.close-button{border:0;background:transparent;font-size:24px;color:#748177}.update-box label{display:block;font-size:12px;color:#77847a;margin-bottom:8px}.fill-input-row{display:flex;align-items:center;gap:10px}.fill-input-row input[type=range]{min-width:0;flex:1;accent-color:#3f7650}.number-input{width:65px;padding:7px;border:1px solid #dce5dd;border-radius:8px}.fill-input-row>span{color:#758178}.update-button{width:100%;border:0;background:#244b34;color:white;font-weight:750;padding:11px;border-radius:10px;margin-top:14px}.update-button:disabled{opacity:.6}.update-message{font-size:12px;color:#497251;margin-bottom:0}
.forecast-panel,.routes-panel{padding-bottom:22px}.forecast-grid{padding:20px 24px 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.forecast-card{padding:17px;border:1px solid #e6ebe6;border-radius:15px;background:#fff}.forecast-top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}.forecast-top>div:first-child{display:grid;gap:4px;min-width:0}.forecast-top>div:first-child span{font-size:11px;color:#8a958d}.forecast-top>div:first-child strong{font-size:13px;overflow-wrap:anywhere}.risk-badge{font-size:10px;font-weight:800;padding:6px 8px;border-radius:8px;background:#f1f4f1;color:#66756a;white-space:nowrap}.risk-critical{background:#fff0ef;color:#bd3e36}.risk-high{background:#fff3e8;color:#c45a24}.risk-medium{background:#fff8e5;color:#9a7418}.risk-low{background:#edf8ef;color:#39824a}.forecast-current{display:flex;align-items:baseline;gap:8px;margin:19px 0 14px}.forecast-current strong{font-size:28px;letter-spacing:-.7px}.forecast-current span{font-size:11px;color:#8d988f}.forecast-details{display:grid;grid-template-columns:1fr 1fr;gap:8px}.forecast-details>div{display:grid;gap:5px}.forecast-details span{font-size:10px;color:#8d988f}.forecast-details strong{font-size:12px}.forecast-warning{border-top:1px solid #edf0ed;margin-top:14px;padding-top:12px;color:#66756a;font-size:11px;line-height:1.5}.no-prediction{display:grid;gap:5px;margin-top:16px;color:#77847a;font-size:12px}.no-prediction small{color:#a0a9a2}.calculating{font-size:12px;color:#64816b}
.routes-panel{padding-bottom:24px}.ai-route-summary{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;padding:18px 24px 0}.ai-route-summary>div,.comparison-panel>div{display:flex;flex-direction:column;gap:7px;padding:15px;border:1px solid #e4eae4;border-radius:14px;background:#fbfdfb;min-width:0}.ai-route-summary span,.comparison-panel span{color:#79867d;font-size:11px;line-height:1.4}.ai-route-summary strong,.comparison-panel strong{color:#21392b;font-size:21px;letter-spacing:-.4px;overflow-wrap:anywhere}.comparison-panel{margin:16px 24px 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.comparison-panel p{grid-column:1/-1;margin:0;color:#8a958d;font-size:11px;line-height:1.5}.routes-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;padding:18px 24px 0}.route-card{border:1px solid #e2e9e3;border-radius:16px;padding:18px;background:white}.route-card-top{display:flex;align-items:center;justify-content:space-between}.truck-label{font-size:10px;letter-spacing:1.4px;font-weight:850;color:#63806a}.route-card h4{font-size:26px;margin:7px 0 0;letter-spacing:-.6px}.route-color{width:13px;height:36px;border-radius:99px}.route-stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0;padding:13px 0;border-top:1px solid #edf0ed;border-bottom:1px solid #edf0ed}.route-stats>div{display:grid;gap:5px}.route-stats span{font-size:11px;color:#8b968e}.route-stats strong{font-size:14px}.route-path{display:grid;gap:11px}.route-stop{display:flex;align-items:center;gap:10px;font-size:12px;color:#59685d}.stop-marker{width:23px;height:23px;border:2px solid;border-radius:50%;display:grid;place-items:center;font-size:10px;font-weight:800;flex-shrink:0}.no-routes-message,.error-banner{margin:16px 24px;padding:14px 16px;border-radius:12px;background:#f5f8f5;color:#65736a;font-size:13px}.error-banner{margin:16px auto;max-width:1700px;background:#fff0ef;color:#b63b35}
.system-section{padding:18px 4px 8px}.system-section h3{font-size:23px;letter-spacing:-.6px;margin:0 0 20px}.pipeline{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:22px;background:white;border:1px solid #e1e8e2;border-radius:18px}.pipeline>div{display:grid;gap:6px;flex:1}.pipeline>div>span{font-size:10px;color:#74917a;letter-spacing:1px;font-weight:800}.pipeline strong{font-size:15px}.pipeline p{font-size:12px;color:#8b968e;margin:0}.pipeline>i{font-style:normal;color:#9bad9e;font-size:20px}.footer{display:flex;justify-content:space-between;gap:15px;padding:20px clamp(18px,4vw,64px);background:white;border-top:1px solid #e1e8e2;color:#8b968e;font-size:12px}.footer span:first-child{font-weight:800;color:#4d6252}.loading-screen{min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;background:#f5f8f5}.loading-screen h2{margin:16px 0 4px}.loading-screen p{color:#839087;font-size:13px}.error-banner{display:flex;gap:10px;align-items:center}
@media(max-width:1400px){.stats-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.main-grid{grid-template-columns:minmax(0,1.4fr) minmax(360px,1fr)}.ai-route-summary{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:980px){.main-grid{grid-template-columns:1fr}.map-container{height:450px}.forecast-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.ai-route-summary{grid-template-columns:repeat(3,minmax(0,1fr))}.page-intro{align-items:flex-start}.updated-time{padding-top:20px}}
@media(max-width:650px){.topbar{height:auto;min-height:76px;padding:12px 15px}.brand-logo{width:45px;height:45px;border-radius:14px}.brand h1{font-size:20px}.brand span{font-size:11px}.topbar-right{gap:10px}.system-status{display:none}.refresh-button{padding:10px 12px}.dashboard{padding:20px 12px}.page-intro{display:block}.page-intro h2{font-size:29px}.updated-time{align-items:flex-start;padding-top:14px}.stats-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.stat-card{padding:15px;min-height:135px}.stat-top{font-size:12px;margin-bottom:13px}.stat-card>strong{font-size:29px}.stat-card>small{font-size:11px}.panel-header{padding:18px}.map-container{height:380px}.bin-list{padding:0 12px}.bin-row{grid-template-columns:minmax(0,1fr) auto auto;gap:8px}.bin-fill{min-width:64px}.fill-track{max-width:78px}.edit-bin{padding:8px 10px}.forecast-grid,.routes-grid{grid-template-columns:1fr;padding-left:14px;padding-right:14px}.ai-route-summary{grid-template-columns:repeat(2,minmax(0,1fr));padding:14px}.comparison-panel{grid-template-columns:1fr;margin:14px}.comparison-panel p{grid-column:auto}.ai-route-summary strong,.comparison-panel strong{font-size:19px}.pipeline{flex-wrap:wrap;padding:16px}.pipeline>div{flex:1 1 38%}.pipeline>i{display:none}.footer{padding:17px;flex-direction:column}.panel-header p{font-size:12px}}
`;

// =====================================================
// APP
// =====================================================

function App() {

  const [
    bins,
    setBins
  ] = useState([]);


  const [
    routes,
    setRoutes
  ] = useState([]);


  const [
    aiCandidates,
    setAiCandidates
  ] = useState([]);


  const [
    aiRouteSummary,
    setAiRouteSummary
  ] = useState(null);


  const [
    baselineRoute,
    setBaselineRoute
  ] = useState(null);


  const [
    roadRoutes,
    setRoadRoutes
  ] = useState({});


  const [
    predictions,
    setPredictions
  ] = useState([]);


  const [
    loading,
    setLoading
  ] = useState(true);


  const [
    routeLoading,
    setRouteLoading
  ] = useState(false);


  const [
    predictionLoading,
    setPredictionLoading
  ] = useState(false);


  const [
    error,
    setError
  ] = useState("");


  const [
    selectedBin,
    setSelectedBin
  ] = useState(null);


  const [
    newFill,
    setNewFill
  ] = useState("");


  const [
    updating,
    setUpdating
  ] = useState(false);


  const [
    updateMessage,
    setUpdateMessage
  ] = useState("");


  const [
    lastUpdated,
    setLastUpdated
  ] = useState(null);


  // ===================================================
  // LOAD BINS
  // ===================================================

  async function loadBins() {

    try {

      const response =
        await fetch(
          `${API}/bins`
        );


      if (!response.ok) {

        throw new Error(
          "Failed to load bins"
        );
      }


      const data =
        await response.json();


      setBins(data);


      setLastUpdated(
        new Date()
      );


      setError("");


    } catch (err) {

      console.error(err);

      setError(
        "Unable to connect to SmartWaste backend."
      );
    }
  }


  // ===================================================
  // ===================================================
  // LOAD AI-OPTIMIZED ROUTES
  // ===================================================

  async function loadRoutes() {

    try {

      setRouteLoading(true);

      const [response, baselineResponse] = await Promise.all([
        fetch(`${API}/ai-vrp-route`),
        fetch(`${API}/vrp-route`).catch(() => null)
      ]);

      if (!response.ok) {
        let detail = "";
        try {
          const errorData = await response.json();
          detail = errorData.detail || errorData.message || "";
        } catch {
          // The server may return a non-JSON error response.
        }
        throw new Error(
          detail
            ? `AI route API error: ${detail}`
            : `AI route API returned HTTP ${response.status}`
        );
      }

      const data = await response.json();

      if (baselineResponse?.ok) {
        const baselineData = await baselineResponse.json();
        setBaselineRoute(baselineData);
      } else {
        setBaselineRoute(null);
      }

      setRoutes(data.routes || []);
      setAiCandidates(data.candidates || []);
      setAiRouteSummary({
        truckCapacity: data.truck_capacity_kg ?? 200,
        trucksUsed: data.trucks_used ?? (data.routes || []).length,
        totalDistance: data.total_distance_km ?? 0,
        selectedBins: data.total_selected_bins ?? 0,
        estimatedWaste: (data.routes || []).reduce(
          (total, route) => total + Number(route.load_kg || 0),
          0
        ),
        message: data.message || ""
      });

      setError("");

    } catch (err) {

      console.error(err);

      setError(
        err?.message ||
          "Unable to calculate AI-optimized routes. Check the backend and CORS settings."
      );

    } finally {

      setRouteLoading(false);
    }
  }


  // LOAD PREDICTIONS
  // ===================================================

  async function loadPredictions() {

    try {

      setPredictionLoading(true);


      const response =
        await fetch(
          `${API}/predictions`
        );


      if (!response.ok) {

        throw new Error(
          "Prediction request failed"
        );
      }


      const data =
        await response.json();


      setPredictions(
        data || []
      );


    } catch (err) {

      console.error(
        "Prediction error:",
        err
      );


    } finally {

      setPredictionLoading(false);
    }
  }


  // ===================================================
  // INITIAL LOAD
  // ===================================================

  useEffect(() => {

    async function initialize() {

      setLoading(true);


      await loadBins();

      await loadRoutes();

      await loadPredictions();


      setLoading(false);
    }


    initialize();

  }, []);


  // ===================================================
  // FIND BIN
  // ===================================================

  function getBin(binId) {

    return bins.find(
      (bin) =>
        bin.bin_id === binId
    );
  }


  // ===================================================
  // GET PREDICTION
  // ===================================================

  function getPrediction(binId) {

    return predictions.find(
      (prediction) =>
        prediction.bin_id === binId
    );
  }


  // ===================================================
  // ROAD ROUTES
  // ===================================================

  useEffect(() => {

    if (
      !routes.length ||
      !bins.length
    ) {

      return;
    }


    async function loadRoadRoutes() {

      const newRoadRoutes = {};


      for (
        const route of routes
      ) {

        try {

          const coordinates = [];


          for (
            const stop of route.route
          ) {

            if (
              stop === "Depot"
            ) {

              coordinates.push(
                DEPOT
              );


            } else {

              const bin =
                getBin(stop);


              if (bin) {

                coordinates.push([
                  bin.location.latitude,
                  bin.location.longitude,
                ]);

              }
            }
          }


          if (
            coordinates.length < 2
          ) {

            continue;
          }


          const osrmCoordinates =
            coordinates
              .map(
                ([lat, lon]) =>
                  `${lon},${lat}`
              )
              .join(";");


          const url =
            `https://router.project-osrm.org/route/v1/driving/` +
            `${osrmCoordinates}` +
            `?overview=full&geometries=geojson`;


          const response =
            await fetch(url);


          if (!response.ok) {

            throw new Error(
              "OSRM request failed"
            );
          }


          const data =
            await response.json();


          if (
            data.code !== "Ok" ||
            !data.routes?.length
          ) {

            throw new Error(
              "No road route returned"
            );
          }


          const roadCoordinates =
            data.routes[0]
              .geometry
              .coordinates
              .map(
                ([lon, lat]) =>
                  [lat, lon]
              );


          newRoadRoutes[
            route.truck
          ] =
            roadCoordinates;


        } catch (err) {

          console.error(err);


          const fallback = [];


          for (
            const stop of route.route
          ) {

            if (
              stop === "Depot"
            ) {

              fallback.push(
                DEPOT
              );


            } else {

              const bin =
                getBin(stop);


              if (bin) {

                fallback.push([
                  bin.location.latitude,
                  bin.location.longitude,
                ]);

              }
            }
          }


          newRoadRoutes[
            route.truck
          ] =
            fallback;
        }
      }


      setRoadRoutes(
        newRoadRoutes
      );
    }


    loadRoadRoutes();

  }, [
    routes,
    bins
  ]);


  // ===================================================
  // UPDATE BIN
  // ===================================================

  async function updateBin() {

    if (!selectedBin) {

      return;
    }


    const value =
      Number(newFill);


    if (
      Number.isNaN(value) ||
      value < 0 ||
      value > 100
    ) {

      setUpdateMessage(
        "Enter a value between 0 and 100."
      );

      return;
    }


    try {

      setUpdating(true);

      setUpdateMessage("");


      const response =
        await fetch(

          `${API}/bins/${selectedBin.bin_id}/fill`,

          {

            method:
              "PUT",

            headers: {

              "Content-Type":
                "application/json"
            },

            body:
              JSON.stringify({

                fill_percent:
                  value
              })
          }
        );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Failed to update bin"
        );
      }


      setUpdateMessage(
        `${selectedBin.bin_id} updated successfully`
      );


      setSelectedBin(
        null
      );


      setNewFill(
        ""
      );


      // Reload everything

      await loadBins();

      await loadRoutes();

      await loadPredictions();


    } catch (err) {

      console.error(err);

      setUpdateMessage(
        err.message ||
        "Unable to update bin."
      );


    } finally {

      setUpdating(false);
    }
  }


  // ===================================================
  // STATISTICS
  // ===================================================

  const totalBins =
    bins.length;


  const criticalBins =
    bins.filter(
      (bin) =>
        bin.priority ===
        "CRITICAL"
    ).length;


  const highBins =
    bins.filter(
      (bin) =>
        bin.priority ===
        "HIGH"
    ).length;


  const totalWaste =
    bins.reduce(

      (sum, bin) =>
        sum +
        Number(
          bin.estimated_waste_kg ||
          0
        ),

      0
    );


  const totalDistance =
    routes.reduce(

      (sum, route) =>
        sum +
        Number(
          route.distance_km ||
          0
        ),

      0
    );


  const trucksUsed =
    routes.length;


  const averageFill =
    bins.length

      ? (

          bins.reduce(

            (sum, bin) =>
              sum +
              Number(
                bin.current_fill_percent ||
                0
              ),

            0
          )

          /

          bins.length

        ).toFixed(0)

      : 0;


  // ===================================================
  // SORT BINS
  // ===================================================

  const sortedBins =
    useMemo(

      () => {

        return [
          ...bins
        ].sort(

          (a, b) =>

            Number(
              b.current_fill_percent
            )

            -

            Number(
              a.current_fill_percent
            )
        );

      },

      [bins]
    );


  // ===================================================
  // LOADING
  // ===================================================

  if (loading) {

    return (

      <div className="loading-screen">

        <div className="loading-logo">
          ♻
        </div>

        <h2>
          SmartWaste
        </h2>

        <p>
          Loading city intelligence...
        </p>

      </div>
    );
  }


  // ===================================================
  // UI
  // ===================================================

  return (

    <>
      <style>{APP_STYLES}</style>
      <div className="app">


      {/* ============================================= */}
      {/* HEADER */}
      {/* ============================================= */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-logo">
            ♻
          </div>

          <div>

            <h1>
              SmartWaste
            </h1>

            <span>
              Intelligent waste operations
            </span>

          </div>

        </div>


        <div className="topbar-right">

          <div className="system-status">

            <span className="online-dot"></span>

            System operational

          </div>


          <button
            className="refresh-button"
            onClick={async () => {

              await loadBins();

              await loadRoutes();

              await loadPredictions();

            }}
          >

            ↻ Refresh

          </button>

        </div>

      </header>


      {/* ============================================= */}
      {/* ERROR */}
      {/* ============================================= */}

      {error && (

        <div className="error-banner">

          <span>!</span>

          {error}

        </div>

      )}


      <main className="dashboard">


        {/* =========================================== */}
        {/* INTRO */}
        {/* =========================================== */}

        <section className="page-intro">

          <div>

            <p className="eyebrow">
              BENGALURU · LIVE OPERATIONS
            </p>

            <h2>
              Waste collection overview
            </h2>

            <p className="intro-text">

              Monitor fill levels, predict
              collection risk and optimize
              truck routes from one dashboard.

            </p>

          </div>


          <div className="updated-time">

            <span>
              Last synchronized
            </span>

            <strong>

              {lastUpdated
                ? lastUpdated.toLocaleTimeString()
                : "--"}

            </strong>

          </div>

        </section>


        {/* =========================================== */}
        {/* STATS */}
        {/* =========================================== */}

        <section className="stats-grid">


          <div className="stat-card">

            <div className="stat-top">

              <span>
                Monitored bins
              </span>

              <div className="stat-icon">
                ▦
              </div>

            </div>

            <strong>
              {totalBins}
            </strong>

            <small>
              Active collection points
            </small>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <span>
                Average fill
              </span>

              <div className="stat-icon">
                ◔
              </div>

            </div>

            <strong>
              {averageFill}%
            </strong>

            <small>
              Across monitored bins
            </small>

          </div>


          <div className="stat-card stat-alert">

            <div className="stat-top">

              <span>
                Critical
              </span>

              <div className="stat-icon">
                !
              </div>

            </div>

            <strong>
              {criticalBins}
            </strong>

            <small>
              Immediate collection
            </small>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <span>
                High priority
              </span>

              <div className="stat-icon">
                ↑
              </div>

            </div>

            <strong>
              {highBins}
            </strong>

            <small>
              Elevated collection need
            </small>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <span>
                Estimated waste
              </span>

              <div className="stat-icon">
                ♻
              </div>

            </div>

            <strong>

              {totalWaste}

              <small className="unit">
                kg
              </small>

            </strong>

            <small>
              Current estimated load
            </small>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <span>
                Route distance
              </span>

              <div className="stat-icon">
                ↗
              </div>

            </div>

            <strong>

              {totalDistance.toFixed(1)}

              <small className="unit">
                km
              </small>

            </strong>

            <small>
              Optimized collection route
            </small>

          </div>

        </section>


        {/* =========================================== */}
        {/* MAP + BIN MONITOR */}
        {/* =========================================== */}

        <section className="main-grid">


          {/* MAP */}

          <div className="panel map-panel">

            <div className="panel-header">

              <div>

                <h3>
                  Collection network
                </h3>

                <p>
                  Live bin locations and road routes
                </p>

              </div>


              <div className="map-status">

                <span className="online-dot"></span>

                Live

              </div>

            </div>


            <div className="map-container">

              <MapContainer

                center={[
                  12.925,
                  77.60
                ]}

                zoom={12}

                scrollWheelZoom={true}

                style={{
                  height: "100%",
                  width: "100%"
                }}

              >

                <MapResizeHandler />


                <TileLayer

                  attribution="&copy; OpenStreetMap contributors"

                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

                />


                {/* DEPOT */}

                <Marker

                  position={DEPOT}

                  icon={
                    createDepotIcon()
                  }

                >

                  <Popup>

                    <div className="popup-content">

                      <strong>
                        Collection Depot
                      </strong>

                      <span>
                        Bengaluru Central
                      </span>

                    </div>

                  </Popup>

                </Marker>


                {/* BINS */}

                {bins.map(
                  (bin) => (

                    <Marker

                      key={
                        bin.bin_id
                      }

                      position={[
                        bin.location.latitude,
                        bin.location.longitude
                      ]}

                      icon={
                        createBinIcon(
                          bin.current_fill_percent,
                          bin.priority
                        )
                      }

                    >

                      <Popup>

                        <div className="popup-content">

                          <strong>
                            {bin.bin_id}
                          </strong>

                          <span>
                            {bin.location.name}
                          </span>

                          <div className="popup-divider"></div>

                          <div className="popup-row">

                            <span>
                              Fill
                            </span>

                            <strong>
                              {bin.current_fill_percent}%
                            </strong>

                          </div>


                          <div className="popup-row">

                            <span>
                              Priority
                            </span>

                            <strong
                              style={{
                                color:
                                  getPriorityColor(
                                    bin.priority
                                  )
                              }}
                            >
                              {bin.priority}
                            </strong>

                          </div>


                          <div className="popup-row">

                            <span>
                              Waste
                            </span>

                            <strong>
                              {bin.estimated_waste_kg} kg
                            </strong>

                          </div>

                        </div>

                      </Popup>

                    </Marker>

                  )
                )}


                {/* ROAD ROUTES */}

                {Object.entries(
                  roadRoutes
                ).map(

                  ([
                    truckNumber,
                    coordinates
                  ]) => (

                    <Polyline

                      key={
                        truckNumber
                      }

                      positions={
                        coordinates
                      }

                      pathOptions={{

                        color:
                          ROUTE_COLORS[
                            (
                              Number(
                                truckNumber
                              ) - 1
                            )
                            %
                            ROUTE_COLORS.length
                          ],

                        weight: 5,

                        opacity: 0.82

                      }}

                    />

                  )
                )}

              </MapContainer>


              <div className="map-legend">

                <span className="legend-title">
                  Bin status
                </span>

                <div>
                  <i className="legend critical"></i>
                  Critical
                </div>

                <div>
                  <i className="legend high"></i>
                  High
                </div>

                <div>
                  <i className="legend medium"></i>
                  Medium
                </div>

                <div>
                  <i className="legend normal"></i>
                  Normal
                </div>

              </div>

            </div>

          </div>


          {/* BIN PANEL */}

          <div className="panel bin-panel">

            <div className="panel-header">

              <div>

                <h3>
                  Bin monitoring
                </h3>

                <p>
                  Highest fill levels first
                </p>

              </div>

              <span className="bin-count">
                {bins.length}
              </span>

            </div>


            <div className="bin-list">

              {sortedBins.map(
                (bin) => {

                  const fill =
                    Number(
                      bin.current_fill_percent
                    );


                  const prediction =
                    getPrediction(
                      bin.bin_id
                    );


                  return (

                    <div
                      className="bin-row"
                      key={
                        bin.bin_id
                      }
                    >

                      <div className="bin-row-main">

                        <div

                          className="mini-status"

                          style={{
                            background:
                              getPriorityColor(
                                bin.priority
                              )
                          }}

                        ></div>


                        <div className="bin-info">

                          <strong>
                            {bin.bin_id}
                          </strong>

                          <span>
                            {bin.location.name}
                          </span>

                          {(() => {
                            const ai = aiCandidates.find(
                              (item) => item.bin_id === bin.bin_id
                            );

                            return ai ? (
                              <span className="ai-priority-inline">
                                AI: {ai.ai_priority} · Score {ai.ai_priority_score}
                              </span>
                            ) : null;
                          })()}

                        </div>

                      </div>


                      <div className="bin-fill">

                        <strong>
                          {fill}%
                        </strong>

                        <div className="fill-track">

                          <div

                            className="fill-bar"

                            style={{
                              width:
                                `${fill}%`,

                              background:
                                getPriorityColor(
                                  bin.priority
                                )
                            }}

                          ></div>

                        </div>

                      </div>


                      <button

                        className="edit-bin"

                        onClick={() => {

                          setSelectedBin(
                            bin
                          );

                          setNewFill(
                            String(fill)
                          );

                          setUpdateMessage("");

                        }}

                      >
                        Edit
                      </button>


                      {prediction?.prediction_available && (

                        <div className="prediction-mini">

                          <span>
                            AI forecast
                          </span>

                          <strong>

                            {prediction
                              .fill_rate_percent_per_hour
                              >= 0
                              ? "+"
                              : ""}

                            {prediction
                              .fill_rate_percent_per_hour}

                            %/hr

                          </strong>

                        </div>

                      )}

                    </div>

                  );

                }
              )}

            </div>


            {/* UPDATE */}

            {selectedBin && (

              <div className="update-box">

                <div className="update-header">

                  <div>

                    <span>
                      UPDATE BIN
                    </span>

                    <strong>
                      {selectedBin.bin_id}
                    </strong>

                  </div>


                  <button

                    className="close-button"

                    onClick={() =>
                      setSelectedBin(null)
                    }

                  >
                    ×
                  </button>

                </div>


                <label>
                  Fill percentage
                </label>


                <div className="fill-input-row">

                  <input

                    type="range"

                    min="0"

                    max="100"

                    value={
                      newFill || 0
                    }

                    onChange={(e) =>
                      setNewFill(
                        e.target.value
                      )
                    }

                  />


                  <input

                    className="number-input"

                    type="number"

                    min="0"

                    max="100"

                    value={
                      newFill
                    }

                    onChange={(e) =>
                      setNewFill(
                        e.target.value
                      )
                    }

                  />

                  <span>
                    %
                  </span>

                </div>


                <button

                  className="update-button"

                  onClick={
                    updateBin
                  }

                  disabled={
                    updating
                  }

                >

                  {updating
                    ? "Updating..."
                    : "Update & Recalculate"}

                </button>


                {updateMessage && (

                  <p className="update-message">

                    {updateMessage}

                  </p>

                )}

              </div>

            )}

          </div>

        </section>


        {/* =========================================== */}
        {/* AI FORECAST */}
        {/* =========================================== */}

        <section className="panel forecast-panel">

          <div className="panel-header">

            <div>

              <h3>
                AI fill-level forecast
              </h3>

              <p>
                Historical trend analysis and predicted
                collection risk
              </p>

            </div>


            {predictionLoading && (

              <span className="calculating">
                Analyzing...
              </span>

            )}

          </div>


          <div className="forecast-grid">

            {sortedBins.map(
              (bin) => {

                const prediction =
                  getPrediction(
                    bin.bin_id
                  );


                return (

                  <div
                    className="forecast-card"
                    key={
                      bin.bin_id
                    }
                  >

                    <div className="forecast-top">

                      <div>

                        <span>
                          {bin.bin_id}
                        </span>

                        <strong>
                          {bin.location.name}
                        </strong>

                      </div>


                      <div
                        className={
                          `risk-badge risk-${(
                            prediction?.overflow_risk ||
                            "LOW"
                          )
                            .toLowerCase()
                            .replace(
                              " ",
                              "-"
                            )}`
                        }
                      >

                        {prediction?.overflow_risk ||
                          "NO DATA"}

                      </div>

                    </div>


                    <div className="forecast-current">

                      <strong>
                        {bin.current_fill_percent}%
                      </strong>

                      <span>
                        current fill
                      </span>

                    </div>


                    {prediction?.prediction_available ? (

                      <>

                        <div className="forecast-details">

                          <div>

                            <span>
                              Fill rate
                            </span>

                            <strong>

                              {prediction
                                .fill_rate_percent_per_hour
                                >= 0
                                ? "+"
                                : ""}

                              {prediction
                                .fill_rate_percent_per_hour}

                              % / hr

                            </strong>

                          </div>


                          <div>

                            <span>
                              Next hour
                            </span>

                            <strong>

                              {prediction
                                .predicted_fill_next_hour}%

                            </strong>

                          </div>

                        </div>


                        <div className="forecast-warning">

                          {prediction.hours_to_90_percent !== null

                            ? prediction.hours_to_90_percent <= 0

                              ? "Collection threshold reached"

                              : `Estimated ${prediction.hours_to_90_percent} hours to 90%`

                            : "No immediate 90% threshold predicted"}

                        </div>

                      </>

                    ) : (

                      <div className="no-prediction">

                        <span>
                          AI forecast unavailable
                        </span>

                        <small>
                          Add more historical readings
                        </small>

                      </div>

                    )}

                  </div>

                );

              }
            )}

          </div>

        </section>


        {/* =========================================== */}
        {/* ROUTES */}
        {/* =========================================== */}

        <section className="panel routes-panel">

          <div className="panel-header">

            <div>

              <h3>
                Optimized collection plan
              </h3>

              <p>
                AI-ranked collection candidates with OR-Tools capacity optimization.
                Map lines use road routing when available.
              </p>

            </div>


            {routeLoading && (

              <span className="calculating">
                Recalculating...
              </span>

            )}

          </div>


          {aiRouteSummary && (
            <div className="ai-route-summary">
              <div>
                <span>AI-selected bins</span>
                <strong>{aiRouteSummary.selectedBins}</strong>
              </div>
              <div>
                <span>Trucks dispatched</span>
                <strong>{aiRouteSummary.trucksUsed}</strong>
              </div>
              <div>
                <span>Waste planned for collection</span>
                <strong>{aiRouteSummary.estimatedWaste} kg</strong>
              </div>
              <div>
                <span>Truck capacity</span>
                <strong>{aiRouteSummary.truckCapacity} kg each</strong>
              </div>
              <div>
                <span>Estimated total distance</span>
                <strong>{Number(aiRouteSummary.totalDistance).toFixed(2)} km</strong>
              </div>
            </div>
          )}

          {aiRouteSummary?.message && (
            <div className="no-routes-message">
              {aiRouteSummary.message}
            </div>
          )}

          {baselineRoute && (
            <div className="comparison-panel">
              <div>
                <span>Standard VRP distance</span>
                <strong>{Number(baselineRoute.total_distance_km || 0).toFixed(2)} km</strong>
              </div>
              <div>
                <span>AI route distance</span>
                <strong>{Number(aiRouteSummary?.totalDistance || 0).toFixed(2)} km</strong>
              </div>
              <div>
                <span>Distance difference</span>
                <strong>
                  {(Number(baselineRoute.total_distance_km || 0) -
                    Number(aiRouteSummary?.totalDistance || 0)).toFixed(2)} km
                </strong>
              </div>
              <p>
                Comparison is indicative: the standard and AI optimizers may select different bins.
                Distances are straight-line estimates, while map paths may follow roads.
              </p>
            </div>
          )}

          <div className="routes-grid">

            {routes.map(
              (route, index) => {

                const color =
                  ROUTE_COLORS[
                    index %
                    ROUTE_COLORS.length
                  ];


                return (

                  <div
                    className="route-card"
                    key={
                      route.truck
                    }
                  >

                    <div className="route-card-top">

                      <div>

                        <span className="truck-label">
                          TRUCK {index + 1}
                        </span>

                        <h4>
                          {route.load_kg} kg
                        </h4>

                      </div>


                      <div

                        className="route-color"

                        style={{
                          background:
                            color
                        }}

                      ></div>

                    </div>


                    <div className="route-stats">

                      <div>

                        <span>
                          Distance
                        </span>

                        <strong>
                          {route.distance_km.toFixed(2)}
                          {" "}km
                        </strong>

                      </div>


                      <div>

                        <span>
                          Capacity
                        </span>

                        <strong>

                          {Math.round(
                            (
                              route.load_kg /
                              200
                            ) *
                            100
                          )}%

                        </strong>

                      </div>

                    </div>


                    <div className="route-path">

                      {route.route.map(
                        (
                          stop,
                          stopIndex
                        ) => (

                          <div
                            className="route-stop"
                            key={
                              `${route.truck}-${stopIndex}`
                            }
                          >

                            <div

                              className="stop-marker"

                              style={{
                                borderColor:
                                  color
                              }}

                            >

                              {stopIndex + 1}

                            </div>


                            <span>

                              {stop ===
                              "Depot"

                                ? "Collection depot"

                                : stop}

                            </span>

                          </div>

                        )
                      )}

                    </div>

                  </div>

                );
              }
            )}

          </div>

          {!routes.length && !routeLoading && (
            <div className="no-routes-message">
              No bins are currently selected for urgent collection.
              Refresh after bin readings or predictions change.
            </div>
          )}

        </section>


        {/* =========================================== */}
        {/* PIPELINE */}
        {/* =========================================== */}

        <section className="system-section">

          <div>

            <span className="eyebrow">
              SMART CITY PIPELINE
            </span>

            <h3>
              From sensor data to optimized action
            </h3>

          </div>


          <div className="pipeline">

            <div>

              <span>
                01
              </span>

              <strong>
                Monitor
              </strong>

              <p>
                Track fill levels
              </p>

            </div>


            <i>
              →
            </i>


            <div>

              <span>
                02
              </span>

              <strong>
                Predict
              </strong>

              <p>
                Forecast waste growth
              </p>

            </div>


            <i>
              →
            </i>


            <div>

              <span>
                03
              </span>

              <strong>
                Optimize
              </strong>

              <p>
                Allocate trucks
              </p>

            </div>


            <i>
              →
            </i>


            <div>

              <span>
                04
              </span>

              <strong>
                Navigate
              </strong>

              <p>
                Follow real roads
              </p>

            </div>

          </div>

        </section>

      </main>


      <footer className="footer">

        <span>
          SmartWaste
        </span>

        <span>
          AI-driven waste collection optimization
        </span>

      </footer>

      </div>
    </>
  );
}


export default App;