<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { formatGrade, formatDateFr } from "$lib/utils";
	import {
		GraduationCap,
		Award,
		BookOpen,
		RefreshCw,
		Filter,
		CheckCircle2
	} from "lucide-svelte";

	let gradesData = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let selectedMatiere = $state<string>("ALL");

	async function loadGrades(forceRefresh = false) {
		isLoading = true;
		error = "";
		try {
			gradesData = await api.getGrades(forceRefresh);
		} catch (err: any) {
			error = err.message || "Erreur lors de la récupération des notes.";
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadGrades();
	});

	// Liste aplatie de toutes les evaluations
	let allEvaluations = $derived(() => {
		if (!gradesData?.matieres) return [];
		const list: any[] = [];
		for (const mat of gradesData.matieres) {
			for (const ev of mat.evaluations || []) {
				list.push({
					...ev,
					code_matiere: mat.code,
					titre_matiere: mat.titre
				});
			}
		}
		// Tri par date decroissante
		return list.sort((a, b) => (b.date || "").localeCompare(a.date || ""));
	});

	let filteredEvaluations = $derived(() => {
		const all = allEvaluations();
		if (selectedMatiere === "ALL") return all;
		return all.filter((ev) => ev.code_matiere === selectedMatiere);
	});
</script>

<div class="space-y-6">
	<!-- En-tete -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
				<GraduationCap class="w-5 h-5 text-cyan-400" />
				Notes & Relevé ScoDoc
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Moyennes par Unité d'Enseignement (UE), matières (Ressources & SAÉ) et détail des notes saisies.
			</p>
		</div>

		<button
			onclick={() => loadGrades(true)}
			disabled={isLoading}
			class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[#0E121B] hover:bg-[#151C2A] border border-[#182030] text-xs font-medium text-zinc-300 hover:text-white transition-all cursor-pointer"
		>
			<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
			<span>Rafraîchir ScoDoc</span>
		</button>
	</div>

	{#if isLoading && !gradesData}
		<div class="flex flex-col items-center justify-center p-16 text-zinc-400">
			<RefreshCw class="w-7 h-7 animate-spin text-cyan-400 mb-3" />
			<p class="text-xs">Chargement instantané des notes ScoDoc...</p>
		</div>
	{:else if error}
		<div class="p-4 rounded-xl bg-red-950/30 border border-red-800/40 text-red-400 text-xs">
			{error}
		</div>
	{:else if gradesData}
		<!-- Grille des UEs -->
		<div>
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
					<Award class="w-4 h-4 text-cyan-400" />
					<span>Unités d'Enseignement (UE) du Semestre</span>
				</h2>
				{#if gradesData.stats?.moyenne_generale}
					<span class="text-xs text-zinc-400 font-mono">
						Moyenne générale : <strong class="text-cyan-400 font-bold">{formatGrade(gradesData.stats.moyenne_generale)}</strong>
					</span>
				{/if}
			</div>

			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				{#each gradesData.ues || [] as ue}
					<div class="bg-[#0E121B] border border-[#182030] rounded-2xl p-5 space-y-3">
						<div class="flex items-start justify-between">
							<div class="space-y-1">
								<div class="flex items-center gap-2">
									<span class="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
										{ue.code}
									</span>
									<span class="text-[11px] text-zinc-500 font-mono">{ue.ects} ECTS</span>
								</div>
								<h3 class="font-semibold text-xs text-white line-clamp-1" title={ue.titre}>
									{ue.titre}
								</h3>
							</div>

							<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold {ue.moyenne && ue.moyenne >= 10
								? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
								: 'bg-zinc-900 text-zinc-500 border border-zinc-800'}">
								{ue.status}
							</span>
						</div>

						<div class="flex items-baseline justify-between pt-1">
							<div class="flex items-baseline gap-1">
								<span class="text-2xl font-bold font-mono {ue.moyenne && ue.moyenne >= 10 ? 'text-emerald-400' : 'text-zinc-400'}">
									{formatGrade(ue.moyenne)}
								</span>
								<span class="text-xs text-zinc-500">/ 20</span>
							</div>
							<div class="text-xs text-zinc-400">
								Rang : <strong class="text-cyan-400 font-mono font-semibold">{ue.rang || "--"}</strong> / {ue.total_promo || "--"}
							</div>
						</div>

						<!-- Jauge d'avancement vers la validation -->
						<div class="w-full bg-[#151C2A] rounded-full h-1 overflow-hidden">
							<div
								class="h-full rounded-full transition-all duration-500 {ue.moyenne && ue.moyenne >= 10 ? 'bg-emerald-500' : 'bg-zinc-700'}"
								style="width: {Math.min(100, Math.max(0, ((ue.moyenne || 0) / 20) * 100))}%"
							></div>
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Moyennes par Matiere (Ressources & SAEs) avec calcul precis -->
		<div>
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
					<BookOpen class="w-4 h-4 text-cyan-400" />
					<span>Moyennes par Matière (Ressources & SAÉ)</span>
				</h2>
				<span class="text-[11px] text-zinc-500">
					Cliquez sur une matière pour filtrer ses notes
				</span>
			</div>

			<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
				{#each gradesData.matieres || [] as mat}
					{@const isSelected = selectedMatiere === mat.code}
					<button
						onclick={() => (selectedMatiere = isSelected ? "ALL" : mat.code)}
						class="text-left p-3.5 rounded-2xl border transition-all cursor-pointer {isSelected
							? 'border-cyan-500 bg-[#0E2A38] text-white shadow-sm'
							: 'border-[#182030] bg-[#0E121B] hover:border-zinc-700'}"
					>
						<div class="flex items-center justify-between mb-1">
							<span class="font-mono font-bold text-xs {isSelected ? 'text-cyan-300' : 'text-zinc-200'}">
								{mat.code}
							</span>
							<span class="text-[10px] text-zinc-500 font-mono">
								{mat.evaluations_count} éval.
							</span>
						</div>

						<div class="text-lg font-bold font-mono {mat.moyenne && mat.moyenne >= 10 ? 'text-emerald-400' : mat.moyenne ? 'text-amber-400' : 'text-zinc-500'}">
							{mat.moyenne !== null && mat.moyenne !== undefined ? formatGrade(mat.moyenne) : "En attente"}
						</div>

						<div class="text-[10px] text-zinc-400 truncate mt-1" title={mat.titre}>
							{mat.titre}
						</div>
					</button>
				{/each}
			</div>
		</div>

		<!-- Detail des evaluations saisies -->
		<div class="bg-[#0E121B] border border-[#182030] rounded-2xl p-5 space-y-4">
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#182030]">
				<div>
					<h2 class="text-sm font-bold text-white">Détail des Évaluations Saisies</h2>
					<p class="text-xs text-zinc-500 mt-0.5">
						{#if selectedMatiere !== "ALL"}
							Filtré pour la matière <strong class="text-cyan-400">{selectedMatiere}</strong>
						{:else}
							Toutes les notes du semestre
						{/if}
					</p>
				</div>

				<div class="flex items-center gap-2">
					<Filter class="w-3.5 h-3.5 text-zinc-500" />
					<select
						bind:value={selectedMatiere}
						class="rounded-xl border border-[#182030] bg-[#080A0F] px-3 py-1.5 text-xs text-zinc-200 focus:border-cyan-500 focus:outline-none"
					>
						<option value="ALL">Toutes les matières ({allEvaluations().length} notes)</option>
						{#each gradesData.matieres || [] as mat}
							<option value={mat.code}>{mat.code} - {mat.titre} ({mat.evaluations_count})</option>
						{/each}
					</select>
				</div>
			</div>

			<div class="space-y-2.5">
				{#if filteredEvaluations().length === 0}
					<div class="py-12 text-center text-zinc-600 text-xs">
						Aucune note enregistrée pour cette sélection.
					</div>
				{:else}
					{#each filteredEvaluations() as ev}
						<div class="p-3.5 rounded-xl border border-[#182030] bg-[#080A0F] hover:border-zinc-700 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
							<div class="space-y-1">
								<div class="flex items-center gap-2 flex-wrap">
									<span class="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-cyan-400">
										{ev.code_matiere}
									</span>
									<span class="font-semibold text-zinc-200">{ev.description || "Évaluation"}</span>
									<span class="text-[11px] text-zinc-500 font-mono">Coef {ev.coefficient}</span>
								</div>
								<div class="text-[11px] text-zinc-400">
									{ev.titre_matiere}
								</div>
							</div>

							<div class="flex items-center sm:text-right gap-4 justify-between sm:justify-end">
								{#if ev.date}
									<span class="text-[11px] text-zinc-500 font-mono">
										{formatDateFr(ev.date)}
									</span>
								{/if}

								<div class="flex items-baseline gap-1 bg-[#0E121B] px-3 py-1 rounded-xl border border-[#182030]">
									<span class="font-bold text-sm font-mono text-cyan-400">
										{formatGrade(ev.note)}
									</span>
									<span class="text-[10px] text-zinc-500">/ 20</span>
								</div>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</div>
