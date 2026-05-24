import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Runs } from "./pages/Runs";
import { RunDetails } from "./pages/RunDetails";
import { NewRun } from "./pages/NewRun";
import { Results } from "./pages/Results";
import { Compare } from "./pages/Compare";
import { Artifacts } from "./pages/Artifacts";
import { Datasets } from "./pages/Datasets";
import { Configurations } from "./pages/Configurations";
import { Models } from "./pages/Models";
import { Users } from "./pages/Users";
import { Settings } from "./pages/Settings";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/runs" element={<Runs />} />
          <Route element={<ProtectedRoute roles={["admin", "researcher"]} />}>
            <Route path="/runs/new" element={<NewRun />} />
          </Route>
          <Route path="/runs/:id" element={<RunDetails />} />
          <Route path="/results" element={<Results />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/artifacts" element={<Artifacts />} />
          <Route path="/datasets" element={<Datasets />} />
          <Route path="/configs" element={<Configurations />} />
          <Route path="/models" element={<Models />} />
          <Route element={<ProtectedRoute roles={["admin"]} />}>
            <Route path="/users" element={<Users />} />
          </Route>
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
