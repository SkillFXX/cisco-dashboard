<script lang="ts">
	import { Clock, MapPin, User as UserIcon, Users, Plus, CalendarClock } from "lucide-svelte";
	import { api } from "$lib/api";
	import { getCourseColorStyle, getCourseTypeLabel } from "$lib/utils";
	import Modal from "./Modal.svelte";

	let {
		course,
		open = $bindable(false),
		events = undefined,
		onAddTask
	}: {
		course: any;
		open: boolean;
		events?: any[];
		onAddTask?: (course: any) => void;
	} = $props();

	let showUpcoming = $state(false);
	let fetchedEvents = $state<any[] | null>(null);
	let loadingEvents = $state(false);

	// Repli sur l'API (cache serveur) quand le parent ne fournit pas la liste des cours.
	async function toggleUpcoming() {
		showUpcoming = !showUpcoming;
		if (showUpcoming && !events && !fetchedEvents) {
			loadingEvents = true;
			try {
				fetchedEvents = (await api.getTimetableWeek()).all_events || [];
			} catch {
				fetchedEvents = [];
			} finally {
				loadingEvents = false;
			}
		}
	}

	$effect(() => {
		if (!open) showUpcoming = false;
	});

	let upcoming = $derived(() => {
		const list = events ?? fetchedEvents ?? [];
		const localNow = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 19);
		return list
			.filter((e: any) => e.title === course?.title && e.id !== course?.id && e.dt_start > course?.dt_start && e.dt_start > localNow)
			.sort((a: any, b: any) => a.dt_start.localeCompare(b.dt_start))
			.slice(0, 8);
	});

	function shortDate(iso: string): string {
		const [y, m, d] = iso.split("-").map(Number);
		return new Date(y, m - 1, d, 12).toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" });
	}

	function addTask() {
		open = false;
		onAddTask?.(course);
	}

	function formatDateFullFr(isoDate: string): string {
		if (!isoDate) return "";
		try {
			const [y, m, d] = isoDate.split("-").map(Number);
			const date = new Date(y, m - 1, d, 12, 0, 0);
			return date.toLocaleDateString("fr-FR", {
				weekday: "long",
				day: "numeric",
				month: "long",
				year: "numeric"
			});
		} catch {
			return isoDate;
		}
	}
</script>

<Modal bind:open={open} title="" class="max-w-md">
	{#if course}
		<div class="space-y-5">
			<div class="space-y-1.5">
				<div class="flex items-center gap-2 flex-wrap">
					<span class="text-[11px] font-semibold px-2 py-0.5 rounded-md {getCourseColorStyle(course.type)}">
						{getCourseTypeLabel(course.type)}
					</span>
					{#if course.is_current}
						<span class="text-[11px] font-semibold text-cyan-400">En cours</span>
					{/if}
				</div>
				<h2 class="text-base font-bold text-fg leading-snug">{course.title}</h2>
				<p class="text-xs text-muted capitalize">{formatDateFullFr(course.date)}</p>
			</div>

			<dl class="divide-y divide-app-border text-xs border-y border-app-border">
				<div class="flex items-start gap-3 py-2.5">
					<Clock class="w-4 h-4 text-subtle mt-0.5 shrink-0" />
					<dt class="sr-only">Horaires</dt>
					<dd class="text-fg font-medium">{course.start_time} – {course.end_time} <span class="text-muted font-normal">· {course.duration_minutes} min</span></dd>
				</div>
				<div class="flex items-start gap-3 py-2.5">
					<MapPin class="w-4 h-4 text-subtle mt-0.5 shrink-0" />
					<dt class="sr-only">Salle</dt>
					<dd class="text-fg font-medium">{course.location || "Salle non précisée"}</dd>
				</div>
				<div class="flex items-start gap-3 py-2.5">
					<UserIcon class="w-4 h-4 text-subtle mt-0.5 shrink-0" />
					<dt class="sr-only">Enseignant</dt>
					<dd class="text-fg font-medium break-words">{course.teacher || "Enseignant non précisé"}</dd>
				</div>
				<div class="flex items-start gap-3 py-2.5">
					<Users class="w-4 h-4 text-subtle mt-0.5 shrink-0" />
					<dt class="sr-only">Groupe</dt>
					<dd class="text-fg font-medium break-words">{course.group || "Promotion"}</dd>
				</div>
			</dl>

			<div class="flex flex-wrap gap-2">
				{#if onAddTask}
					<button
						type="button"
						onclick={addTask}
						class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-xs font-semibold text-white transition-colors cursor-pointer"
					>
						<Plus class="w-3.5 h-3.5" /> Ajouter un devoir
					</button>
				{/if}
				<button
					type="button"
					onclick={toggleUpcoming}
					aria-expanded={showUpcoming}
					class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-app-raised hover:bg-app-raised2 text-xs font-semibold text-fg transition-colors cursor-pointer"
				>
					<CalendarClock class="w-3.5 h-3.5 text-subtle" /> Prochaines séances
				</button>
			</div>

			{#if showUpcoming}
				<div class="divide-y divide-app-border text-xs">
					{#if loadingEvents}
						<p class="py-2 text-muted">Chargement…</p>
					{:else if upcoming().length === 0}
						<p class="py-2 text-muted">Aucune autre séance prévue pour ce cours.</p>
					{:else}
						{#each upcoming() as s}
							<div class="flex items-center gap-3 py-2">
								<div class="w-24 shrink-0 font-semibold text-fg capitalize">{shortDate(s.date)}</div>
								<div class="text-muted shrink-0">{s.start_time} – {s.end_time}</div>
								<div class="text-subtle truncate">{s.location}</div>
							</div>
						{/each}
					{/if}
				</div>
			{/if}
		</div>
	{/if}
</Modal>
