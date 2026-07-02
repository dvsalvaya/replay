import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { LogOut, LayoutDashboard, Video, Film } from "lucide-react";

export function AppLayout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isDashboard = location.pathname === "/dashboard";

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-50">
      {/* Sidebar */}
      <aside className="hidden w-64 border-r border-slate-800 bg-slate-900/50 p-6 md:flex md:flex-col justify-between">
        <div className="space-y-6">
          <div className="flex items-center gap-2 px-2">
            <Video className="h-6 w-6 text-purple-500" />
            <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
              Sports Highlights
            </span>
          </div>
          <nav className="space-y-1">
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-purple-500/10 text-purple-400"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`
              }
            >
              <LayoutDashboard className="h-4 w-4" />
              Câmera
            </NavLink>
            <NavLink
              to="/gallery"
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-purple-500/10 text-purple-400"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`
              }
            >
              <Film className="h-4 w-4" />
              Galeria
            </NavLink>
          </nav>
        </div>

        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          onClick={logout}
        >
          <LogOut className="h-4 w-4" />
          Sair
        </Button>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900/20 px-6">
          <div className="flex items-center gap-2 md:hidden">
            <Video className="h-5 w-5 text-purple-500" />
            <span className="font-bold text-sm tracking-wider">
              Sports Highlights
            </span>
          </div>

          {/* Navigation link inside header for desktop */}
          <div className="hidden md:flex items-center gap-2">
            <Button
              variant={isDashboard ? "secondary" : "ghost"}
              size="sm"
              onClick={() => navigate("/dashboard")}
              className={
                isDashboard
                  ? "bg-slate-800 text-slate-100 hover:bg-slate-700"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }
            >
              Câmera
            </Button>
            <Button
              variant={!isDashboard ? "secondary" : "ghost"}
              size="sm"
              onClick={() => navigate("/gallery")}
              className={
                !isDashboard
                  ? "bg-slate-800 text-slate-100 hover:bg-slate-700"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }
            >
              Galeria
            </Button>
          </div>

          {/* Navigation link inside header for mobile */}
          <div className="flex items-center gap-1 md:hidden">
            <Button
              variant={isDashboard ? "secondary" : "ghost"}
              size="xs"
              onClick={() => navigate("/dashboard")}
              className={`px-2.5 py-1 text-xs ${
                isDashboard ? "bg-slate-800 text-slate-100" : "text-slate-400"
              }`}
            >
              Câmera
            </Button>
            <Button
              variant={!isDashboard ? "secondary" : "ghost"}
              size="xs"
              onClick={() => navigate("/gallery")}
              className={`px-2.5 py-1 text-xs ${
                !isDashboard ? "bg-slate-800 text-slate-100" : "text-slate-400"
              }`}
            >
              Galeria
            </Button>
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="md:hidden text-slate-400 hover:text-slate-200"
            onClick={logout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sair
          </Button>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="mx-auto max-w-5xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
