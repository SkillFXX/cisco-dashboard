<script lang="ts">
	import { Clock, MapPin, User as UserIcon, Users } from "lucide-svelte";
	import { getCourseBadgeStyle, getCourseTypeLabel } from "$lib/utils";
	import Modal from "./Modal.svelte";

	let { course, open = $bindable(false) }: { course: any; open: boolean } = $props();

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
