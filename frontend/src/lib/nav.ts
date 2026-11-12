import {
	LayoutDashboard,
	Calendar,
	FileText,
	GraduationCap,
	Clock,
	Settings,
	Bell,
	Library,
	ShieldCheck
} from "lucide-svelte";

export interface NavItem {
	id: string;
	label: string;
	icon: any;
	adminOnly?: boolean;
	/** Affiché dans la barre du bas sur mobile (sinon dans le menu « Plus ») */
	primary?: boolean;
}

export const navItems: NavItem[] = [
	{ id: "dashboard", label: "Tableau de bord", icon: LayoutDashboard, primary: true },
	{ id: "timetable", label: "Emploi du temps", icon: Calendar, primary: true },
	{ id: "grades", label: "Notes", icon: FileText, primary: true },
	{ id: "tasks", label: "Devoirs", icon: GraduationCap, primary: true },
	{ id: "resources", label: "Ressources", icon: Library },
	{ id: "absences", label: "Absences", icon: Clock },
	{ id: "notifications", label: "Notifications", icon: Bell },
	{ id: "settings", label: "Paramètres", icon: Settings },
	{ id: "admin", label: "Administration", icon: ShieldCheck, adminOnly: true }
];
