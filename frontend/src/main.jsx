import React from "react";
import ReactDOM from "react-dom/client";
import { withStreamlitConnection } from "streamlit-component-lib";
import AutomataEditor from "./AutomataEditor.jsx";

function App({ args }) {
  return <AutomataEditor args={args} />;
}

const Wrapped = withStreamlitConnection(App);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Wrapped />
  </React.StrictMode>
);
