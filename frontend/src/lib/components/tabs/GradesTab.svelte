<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Badge from "../Badge.svelte";
	import Button from "../Button.svelte";
	import { api } from "$lib/api";
	import { formatGrade, formatDateFr } from "$lib/utils";
	import { GraduationCap, Award, BookOpen, Layers, RefreshCw, Filter } from "lucide-svelte";

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

	let filteredEvaluations = $derived(() => {
		if (!gradesData?.grades) return [];
		if (selectedMatiere === "ALL") return gradesData.grades;
		return gradesData.grades.filter((g: any) => g.code_matiere === selectedMatiere);
	});
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
				<GraduationCap class="w-6 h-6 text-cyan-400" />
				Notes & Relevé ScoDoc
			</h1>
			<p class="text-sm text-zinc-400 mt-1">
				Consultez vos moyennes par Unité d'Enseignement (UE), coefficients, rangs et détail des évaluations.
			</p>
		</div>

		<Button variant="outline" size="sm" onclick={() => loadGrades(true)} disabled={isLoading}>
			<RefreshCw class="w-4 h-4 {isLoading ? 'animate-spin' : ''}" />
			<span>Rafraîchir ScoDoc</span>
		</Button>
	</div>

	{#if isLoading}
		<div class="flex flex-col items-center justify-center p-12 text-zinc-400">
			<RefreshCw class="w-8 h-8 animate-spin text-cyan-400 mb-3" />
			<p class="text-sm">Chargement des données de scolarité ScoDoc...</p>
		</div>
	{:else if error}
		<div class="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
			{error}
		</div>
	{:else if gradesData}
		<!-- UEs Cards Grid -->
		<div>
			<h2 class="text-sm font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
				<Award class="w-4 h-4 text-cyan-400" />
				Unités d'Enseignement (UE) du Semestre
			</h2>
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				{#each gradesData.ues || [] as ue}
					<Card class="space-y-3 relative overflow-hidden border-zinc-800">
						<div class="flex items-start justify-between">
							<div>
								<div class="flex items-center gap-2">
									<Badge variant="cisco" class="font-mono">{ue.code}</Badge>
									<span class="text-xs text-zinc-400">{ue.ects} ECTS</span>
								</div>
								<h3 class="font-semibold text-sm text-white mt-1.5 line-clamp-1" title={ue.titre}>
									{ue.titre}
								</h3>
							</div>
							<Badge variant={ue.moyenne >= 10 ? 'success' : 'destructive'}>
								{ue.status}
							</Badge>
						</div>

						<div class="flex items-baseline justify-between pt-2">
							<div class="flex items-baseline gap-1.5">
								<span class="text-2xl font-bold {ue.moyenne >= 10 ? 'text-emerald-400' : 'text-red-400'}">
									{formatGrade(ue.moyenne)}
								</span>
								<span class="text-xs text-zinc-500">/ 20</span>
							</div>
							<div class="text-xs text-zinc-400">
								Rang : <strong class="text-cyan-400">{ue.rang || "--"}</strong> / {ue.total_promo || "--"}
							</div>
						</div>

						<!-- Progress bar towards 10/20 -->
						<div class="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
							<div
								class="h-full rounded-full transition-all duration-500 {ue.moyenne >= 10 ? 'bg-emerald-500' : 'bg-red-500'}"
								style="width: {Math.min(100, Math.max(0, (ue.moyenne / 20) * 100))}%"
							></div>
						</div>
					</Card>
				{/each}
			</div>
		</div>

		<!-- Matières R&T (Ressources & SAÉ) -->
		<div>
			<h2 class="text-sm font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
				<BookOpen class="w-4 h-4 text-cyan-400" />
				Moyennes par Matière (Ressources & SAÉ)
			</h2>
			<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
				{#each gradesData.matieres || [] as mat}
					<button
						onclick={() => (selectedMatiere = selectedMatiere === mat.code ? "ALL" : mat.code)}
						class="text-left p-3 rounded-xl border transition-all cursor-pointer {selectedMatiere === mat.code ? 'border-cyan-500 bg-cyan-950/30' : 'border-zinc-800/80 bg-zinc-900/60 hover:border-zinc-700'}"
					>
						<div class="flex items-center justify-between mb-1">
							<span class="font-mono font-bold text-xs text-zinc-200">{mat.code}</span>
							<span class="text-[10px] text-zinc-500">{mat.evaluations_count} éval.</span>
						</div>
						<div class="text-lg font-extrabold {mat.moyenne && mat.moyenne >= 10 ? 'text-emerald-400' : 'text-zinc-400'}">
							{formatGrade(mat.moyenne)}
						</div>
						<div class="text-[11px] text-zinc-400 truncate mt-1" title={mat.titre}>
							{mat.titre}
						</div>
					</button>
				{/each}
			</div>
		</div>

		<!-- Detailed Evaluations List -->
		<Card>
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-zinc-800">
				<div>
					<h2 class="text-base font-semibold text-white">Détail des Évaluations Saisies</h2>
					<p class="text-xs text-zinc-400 mt-0.5">
						{#if selectedMatiere !== "ALL"}
							Filtré pour la matière <strong>{selectedMatiere}</strong>
						{:else}
							Toutes les évaluations du semestre
						{/if}
					</p>
				</div>

				<div class="flex items-center gap-2">
					<Filter class="w-4 h-4 text-zinc-400" />
					<select
						bind:value={selectedMatiere}
						class="rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-200 focus:border-cyan-500 focus:outline-none"
					>
						<option value="ALL">Toutes les matières</option>
						{#each gradesData.matieres || [] as mat}
							<option value={mat.code}>{mat.code} - {mat.titre}</option>
						{/each}
					</select>
				</div>
			</div>

			<div class="space-y-2.5">
				{#if filteredEvaluations().length === 0}
					<p class="text-sm text-zinc-500 text-center py-8">Aucune note enregistrée pour cette sélection.</p>
				{:else}
					{#each filteredEvaluations() as ev}
						<div class="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl border border-zinc-800/80 bg-zinc-950/40 hover:bg-zinc-800/30 transition-colors gap-3">
							<div class="space-y-1">
								<div class="flex items-center gap-2 flex-wrap">
									<Badge variant="secondary" class="font-mono text-xs">{ev.code_matiere}</Badge>
									<span class="font-medium text-sm text-zinc-100">{ev.description}</span>
									<span class="text-xs text-zinc-500">Coef {ev.coefficient}</span>
								</div>
								<div class="text-xs text-zinc-400 flex items-center gap-3">
									<span>{ev.titre_matiere}</span>
									<span>•</span>
									<span class="text-zinc-500">{formatDateFr(ev.date)}</span>
								</div>
							</div>

							<div class="flex items-center justify-between sm:justify-end gap-6 border-t sm:border-t-0 border-zinc-800/60 pt-2 sm:pt-0">
								<div class="text-left sm:text-right text-[11px] text-zinc-500">
									<div>Moy. promo : <span class="text-zinc-400 font-medium">{formatGrade(ev.moy_promo)}</span></div>
									<div>Min : {formatGrade(ev.min_promo)} / Max : {formatGrade(ev.max_promo)}</div>
								</div>

								<div class="text-right shrink-0">
									<span class="text-xl font-black {ev.note !== null && ev.note >= 10 ? 'text-emerald-400' : 'text-red-400'}">
										{formatGrade(ev.note)}
									</span>
									<span class="text-xs text-zinc-500 font-medium">/ 20</span>
								</div>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</Card>
	{/if}
</div>

