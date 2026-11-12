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

/** Fond très translucide (15 %) et liseré plein à gauche : suit le thème clair comme le sombre. */
export function getCourseColorStyle(type: string): string {
	const t = (type || "").toUpperCase();
	if (t === "TP") return "bg-c-tp/15 border-l-[3px] border-c-tp text-fg";
	if (t === "TD") return "bg-c-td/15 border-l-[3px] border-c-td text-fg";
	if (t === "CM") return "bg-c-cm/15 border-l-[3px] border-c-cm text-fg";
	if (t === "DS" || t === "EXAMEN") return "bg-c-ds/15 border-l-[3px] border-c-ds text-fg";
	if (t === "SAE") return "bg-c-sae/15 border-l-[3px] border-c-sae text-fg";
	return "bg-c-other/15 border-l-[3px] border-c-other text-fg";
}

/** Étiquette (badge) du type de cours. */
export function getCourseBadgeStyle(type: string): string {
	const t = (type || "").toUpperCase();
	if (t === "TP") return "bg-c-tp/15 text-c-tp";
	if (t === "TD") return "bg-c-td/15 text-c-td";
	if (t === "CM") return "bg-c-cm/15 text-c-cm";
	if (t === "DS" || t === "EXAMEN") return "bg-c-ds/15 text-c-ds";
	if (t === "SAE") return "bg-c-sae/15 text-c-sae";
	return "bg-c-other/15 text-c-other";
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


/** Courbe lissée (spline cubique monotone) passant par tous les points, sans dépassement entre deux relevés. */
export function smoothPath(pts: { x: number; y: number }[]): string {
	const f = (n: number) => n.toFixed(1);
	if (pts.length === 0) return "";
	if (pts.length < 3) return pts.map((p, i) => `${i === 0 ? "M" : "L"}${f(p.x)},${f(p.y)}`).join(" ");

	const n = pts.length;
	const dx: number[] = [];
	const slope: number[] = [];
	for (let i = 0; i < n - 1; i++) {
		dx.push(pts[i + 1].x - pts[i].x || 1e-6);
		slope.push((pts[i + 1].y - pts[i].y) / dx[i]);
	}
	const m: number[] = [slope[0]];
	for (let i = 1; i < n - 1; i++) {
		m.push(slope[i - 1] * slope[i] <= 0 ? 0 : (slope[i - 1] + slope[i]) / 2);
	}
	m.push(slope[n - 2]);
	// Fritsch–Carlson : limite les tangentes pour garder la monotonie
	for (let i = 0; i < n - 1; i++) {
		if (slope[i] === 0) {
			m[i] = 0;
			m[i + 1] = 0;
			continue;
		}
		const a = m[i] / slope[i];
		const b = m[i + 1] / slope[i];
		const s = a * a + b * b;
		if (s > 9) {
			const t = 3 / Math.sqrt(s);
			m[i] = t * a * slope[i];
			m[i + 1] = t * b * slope[i];
		}
	}
	let d = `M${f(pts[0].x)},${f(pts[0].y)}`;
	for (let i = 0; i < n - 1; i++) {
		const h = dx[i] / 3;
		d += ` C${f(pts[i].x + h)},${f(pts[i].y + m[i] * h)} ${f(pts[i + 1].x - h)},${f(pts[i + 1].y - m[i + 1] * h)} ${f(pts[i + 1].x)},${f(pts[i + 1].y)}`;
	}
	return d;
}
