import React, { useState, useEffect } from "react";
import { getAllOutlets } from "./api";  // ✅ Correct relative path
import MapComponent from "./map";       // ✅ Correct import for Map.js

function App() {
  const [outlets, setOutlets] = useState([]);

  useEffect(() => {
    async function fetchData() {
      const data = await getAllOutlets();
      setOutlets(data);
    }
    fetchData();
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <MapComponent /> 
      <div>
        <h2>List of Locations </h2>
      </div> 
      <ul>
        {outlets.map((outlet) => (
          <li key={outlet.id}>
            <strong>{outlet.name}</strong> - {outlet.address} ({outlet.operating_hours})
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
