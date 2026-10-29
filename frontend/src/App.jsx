import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import MainLayout from "./layouts/MainLayout";

// ==========================================
// Auth
// ==========================================

import Login from "./pages/auth/Login";

// ==========================================
// Protected Route
// ==========================================

import ProtectedRoute from "./components/ProtectedRoute";

// ==========================================
// Dashboard
// ==========================================

import Dashboard from "./pages/dashboard/Dashboard";

// ==========================================
// Training
// ==========================================

import TrainingCalendar from "./pages/training/TrainingCalendar";
import Trainings from "./pages/training/Trainings";
import TrainingDetails from "./pages/training/TrainingDetails";
import CreateTraining from "./pages/training/CreateTraining";

// ==========================================
// Reminders
// ==========================================

import Reminders from "./pages/reminders/Reminders";
import WhatsAppTemplates from "./pages/reminders/WhatsAppTemplates";

// ==========================================
// Post Training
// ==========================================

import PostTraining from "./pages/postTraining/PostTraining";

// ==========================================
// Reports
// ==========================================

import Reports from "./pages/reports/Reports";

// ==========================================
// Excel
// ==========================================

import ExcelImport from "./pages/excel/ExcelImport";

// ==========================================
// Settings
// ==========================================

import Settings from "./pages/settings/Settings";

// ==========================================
// 404
// ==========================================

import NotFound from "./pages/NotFound";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* ==========================================
            PUBLIC ROUTES
        ========================================== */}

        <Route
          path="/login"
          element={<Login />}
        />

        {/* ==========================================
            PROTECTED APPLICATION ROUTES
        ========================================== */}

        <Route element={<ProtectedRoute />}>

          <Route element={<MainLayout />}>

            {/* ======================================
                Dashboard
            ====================================== */}

            <Route
              path="/dashboard"
              element={<Dashboard />}
            />

            {/* ======================================
                Training
            ====================================== */}

            <Route
              path="/calendar"
              element={<TrainingCalendar />}
            />

            <Route
              path="/trainings"
              element={<Trainings />}
            />

            <Route
              path="/trainings/create"
              element={<CreateTraining />}
            />

            <Route
              path="/trainings/:id"
              element={<TrainingDetails />}
            />

            {/* ======================================
                Reminders
            ====================================== */}

            <Route
              path="/reminders"
              element={<Reminders />}
            />

            <Route
              path="/reminders/templates"
              element={<WhatsAppTemplates />}
            />

            {/* ======================================
                Post Training
            ====================================== */}

            <Route
              path="/post-training"
              element={<PostTraining />}
            />

            {/* ======================================
                Reports
            ====================================== */}

            <Route
              path="/reports"
              element={<Reports />}
            />

            {/* ======================================
                Excel Import
            ====================================== */}

            <Route
              path="/excel-import"
              element={<ExcelImport />}
            />

            {/* ======================================
                Settings
            ====================================== */}

            <Route
              path="/settings"
              element={<Settings />}
            />

          </Route>

        </Route>

        {/* ==========================================
            DEFAULT ROUTE
        ========================================== */}

        <Route
          path="/"
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />

        {/* ==========================================
            404
        ========================================== */}

        <Route
          path="*"
          element={<NotFound />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;