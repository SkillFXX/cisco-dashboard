<script lang="ts">
	import { Clock, MapPin, User as UserIcon, Users, Plus, CalendarClock } from "lucide-svelte";
	import { api } from "$lib/api";
	import { getCourseBadgeStyle, getCourseTypeLabel } from "$lib/utils";
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
			<!-- En-tête de la modale -->
			<div class="space-y-2 pb-4 border-b border-app-border">
				<div class="flex items-center gap-2 flex-wrap">
					<span class="text-xs font-bold px-2.5 py-0.5 rounded-full {getCourseBadgeStyle(course.type)}">
						{getCourseTypeLabel(course.type)}
					</span>

					{#if course.is_current}
						<span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-cyan-600 text-white">
							En cours actuellement
						</span>
					{/if}
				</div>

				<h2 class="text-base font-bold text-white">
					{course.title}
				</h2>

				<p class="text-xs text-zinc-400">
					{formatDateFullFr(course.date)}
				</p>
			</div>

			<!-- Informations clés sous forme de grille sobre -->
			<div class="grid grid-cols-2 gap-3 text-xs">
				<!-- Horaires -->
				<div class="p-3 rounded-xl bg-app-surface border border-app-border space-y-1">
					<div class="flex items-center gap-1.5 text-zinc-400">
						<Clock class="w-3.5 h-3.5 text-cyan-400" />
						<span class="text-[11px] font-medium uppercase tracking-wider">Horaires</span>
					</div>
					<div class="text-sm font-bold text-white">
						{course.start_time} - {course.end_time}
					</div>
					<div class="text-[10px] text-zinc-400">
						Durée : <span class="text-white font-medium">{course.duration_minutes} min</span>
					</div>
				</div>

				<!-- Salle / Lieu -->
				<div class="p-3 rounded-xl bg-app-surface border border-app-border space-y-1">
					<div class="flex items-center gap-1.5 text-zinc-400">
						<MapPin class="w-3.5 h-3.5 text-cyan-400" />
						<span class="text-[11px] font-medium uppercase tracking-wider">Lieu / Salle</span>
					</div>
					<div class="text-sm font-bold text-white truncate" title={course.location}>
						{course.location || "Non précisé"}
					</div>
					<div class="text-[10px] text-zinc-400">
						Campus universitaire
					</div>
				</div>

				<!-- Enseignant -->
				<div class="p-3 rounded-xl bg-app-surface border border-app-border space-y-1">
					<div class="flex items-center gap-1.5 text-zinc-400">
						<UserIcon class="w-3.5 h-3.5 text-cyan-400" />
						<span class="text-[11px] font-medium uppercase tracking-wider">Enseignant</span>
					</div>
					<div class="text-sm font-bold text-white break-words" title={course.teacher}>
						{course.teacher || "Non spécifié"}
					</div>
					<div class="text-[10px] text-zinc-400">
						Intervenant
					</div>
				</div>

				<!-- Groupe / Promo -->
				<div class="p-3 rounded-xl bg-app-surface border border-app-border space-y-1">
					<div class="flex items-center gap-1.5 text-zinc-400">
						<Users class="w-3.5 h-3.5 text-cyan-400" />
						<span class="text-[11px] font-medium uppercase tracking-wider">Groupe</span>
					</div>
					<div class="text-sm font-bold text-white break-words" title={course.group}>
						{course.group || "Promotion"}
					</div>
					<div class="text-[10px] text-zinc-400">
						Effectif concerné
					</div>
				</div>
			</div>

			<!-- Actions liées au cours -->
			<div class="flex flex-wrap gap-2">
				{#if onAddTask}
					<button
						type="button"
						onclick={addTask}
						class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-xs font-semibold text-white transition-all cursor-pointer"
					>
						<Plus class="w-3.5 h-3.5" /> Ajouter un devoir
					</button>
				{/if}
				<button
					type="button"
					onclick={toggleUpcoming}
					aria-expanded={showUpcoming}
					class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-app-border bg-app-surface hover:bg-white/[0.04] text-xs font-semibold text-zinc-200 transition-all cursor-pointer"
				>
					<CalendarClock class="w-3.5 h-3.5 text-cyan-400" /> Prochaines séances
				</button>
			</div>

			{#if showUpcoming}
				<div class="rounded-xl border border-app-border bg-app-surface divide-y divide-app-border">
					{#if loadingEvents}
						<p class="p-3 text-xs text-zinc-400">Chargement…</p>
					{:else if upcoming().length === 0}
						<p class="p-3 text-xs text-zinc-400">Aucune autre séance prévue pour ce cours.</p>
					{:else}
						{#each upcoming() as s}
							<div class="flex items-center gap-3 p-2.5 text-xs">
								<div class="w-20 shrink-0 font-semibold text-white capitalize">{shortDate(s.date)}</div>
								<div class="text-zinc-300 shrink-0">{s.start_time} - {s.end_time}</div>
								<div class="text-zinc-500 truncate">{s.location}</div>
							</div>
						{/each}
					{/if}
				</div>
			{/if}

			<!-- Bouton de fermeture -->
			<div class="flex justify-end pt-2 border-t border-app-border">
				<button
					type="button"
					onclick={() => (open = false)}
					class="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white transition-all cursor-pointer"
				>
					Fermer
				</button>
			</div>
		</div>
	{/if}
</Modal>
