import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function formatGrade(grade: number | null | undefined): string {
	if (grade === null || grade === undefined) return "--";
	return grade.toFixed(2).replace(".", ",");
}

export function formatDateFr(dateStr: string | null | undefined): string {
	if (!dateStr) return "";
	try {
		const d = new Date(dateStr);
		return d.toLocaleDateString("fr-FR", {
			day: "2-digit",
			month: "short",
			year: "numeric"
		});
	} catch {
		return dateStr;
	}
}

export function formatDateTimeFr(dateStr: string | null | undefined): string {
	if (!dateStr) return "";
	try {
		const d = new Date(dateStr);
		return d.toLocaleDateString("fr-FR", {
			day: "2-digit",
			month: "short",
			hour: "2-digit",
			minute: "2-digit"
		});
	} catch {
		return dateStr;
	}
}

export function toLocalIsoDate(d: Date): string {
	const year = d.getFullYear();
	const month = String(d.getMonth() + 1).padStart(2, "0");
	const day = String(d.getDate()).padStart(2, "0");
	return `${year}-${month}-${day}`;
}

export function getMondayOfDate(d: Date, weekOffset = 0): Date {
	const copy = new Date(d.getFullYear(), d.getMonth(), d.getDate(), 12, 0, 0);
	const day = (copy.getDay() + 6) % 7; // 0 = Lundi, 6 = Dimanche
	copy.setDate(copy.getDate() - day + weekOffset * 7);
	return copy;
}

/** Aplat de couleur d'un cours (texte blanc), identique dans les deux thèmes. */
export function getCourseColorStyle(type: string): string {
	const t = (type || "").toUpperCase();
	if (t === "TP") return "bg-c-tp text-white";
	if (t === "TD") return "bg-c-td text-white";
	if (t === "CM") return "bg-c-cm text-white";
	if (t === "DS" || t === "EXAMEN") return "bg-c-ds text-white";
	if (t === "SAE") return "bg-c-sae text-white";
	return "bg-c-other text-white";
}

export function getCourseBadgeStyle(type: string): string {
	return getCourseColorStyle(type);
}

export function getCourseTypeLabel(type: string): string {
	const t = (type || "").toUpperCase();
	if (t === "TP") return "Travaux Pratiques (TP)";
	if (t === "TD") return "Travaux Dirigés (TD)";
	if (t === "CM") return "Cours Magistral (CM)";
	if (t === "DS" || t === "EXAMEN") return "Évaluation (DS)";
	if (t === "SAE") return "SAÉ / Projet";
	return "Cours";
}

