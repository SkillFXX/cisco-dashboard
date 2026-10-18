<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { Filter, RefreshCw } from "lucide-svelte";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import EvaluationDetailModal from "../EvaluationDetailModal.svelte";

	let gradesData = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let selectedMatiere = $state<string>("ALL");

	// Modal de détail d'une note
	let selectedEvaluation = $state<any>(null);
	let detailModalOpen = $state(false);

	async function loadGrades(forceRefresh = false) {
		isLoading = true;
		error = "";
		try {
			gradesData = await api.getGrades(forceRefresh);
		} catch (err: any) {
			error = err.message || "Erreur de chargement des notes";
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadGrades();
	});

	let allEvaluations = $derived(() => {
		if (!gradesData || !gradesData.matieres) return [];
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
		list.sort((a, b) => {
			if (a.date && b.date) return b.date.localeCompare(a.date);
			return (b.id || 0) - (a.id || 0);
		});
		return list;
	});

	let filteredEvaluations = $derived(() => {
		const all = allEvaluations();
		if (selectedMatiere === "ALL") return all;
		return all.filter((e) => e.code_matiere === selectedMatiere);
	});

	// Séparation UEs principales et UE Bonus
	let mainUes = $derived(() => {
		if (!gradesData || !gradesData.ues) return [];
		return gradesData.ues.filter((u: any) => !u.code?.includes(".B") && !u.titre?.toLowerCase().includes("bonus"));
	});

	let bonusUes = $derived(() => {
		if (!gradesData || !gradesData.ues) return [];
		return gradesData.ues.filter((u: any) => u.code?.includes(".B") || u.titre?.toLowerCase().includes("bonus"));
	});

	// Matières notées dans la grille principale vs matières non notées minimisées
	let gradedMatieres = $derived(() => {
		if (!gradesData || !gradesData.matieres) return [];
		return gradesData.matieres.filter((m: any) => (m.evaluations_count && m.evaluations_count > 0) || m.moyenne !== null);
	});

	let ungradedMatieres = $derived(() => {
		if (!gradesData || !gradesData.matieres) return [];
		return gradesData.matieres.filter((m: any) => (!m.evaluations_count || m.evaluations_count === 0) && m.moyenne === null);
	});

	function formatGrade(note: any): string {
		if (note === null || note === undefined || note === "") return "--";
		const num = typeof note === "number" ? note : parseFloat(note);
		if (isNaN(num)) return String(note);
		return num.toFixed(2);
	}

	function formatDateFr(isoDate: string): string {
		if (!isoDate) return "";
		try {
			const d = new Date(isoDate);
			return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
		} catch {
			return isoDate;
		}
	}

	function openEvaluationDetail(ev: any) {
		selectedEvaluation = ev;
		detailModalOpen = true;
	}

	function totalEctsAcquis(): number {
		if (!gradesData || !gradesData.ues) return 0;
		return gradesData.ues.reduce((acc: number, ue: any) => {
			return (ue.moyenne && ue.moyenne >= 10) ? acc + (ue.ects || 0) : acc;
		}, 0);
	}

	let ectsAcquis = $derived(() => {
		if (gradesData?.stats?.ects_acquis !== undefined && gradesData?.stats?.ects_acquis !== null) {
			return gradesData.stats.ects_acquis;
		}
		return totalEctsAcquis();
	});

	let ectsTotal = $derived(() => {
		return gradesData?.stats?.ects_total || 30;
	});
</script>

<div class="space-y-6">
	<!-- En-tête de la page -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold text-white tracking-tight">
				Notes & Relevé ScoDoc
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Moyennes par Unité d'Enseignement (UE), matières et analyse comparative dans la promotion.
			</p>
		</div>

		<button
			onclick={() => loadGrades(true)}
			disabled={isLoading}
			class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-app-card hover:bg-zinc-800 border border-app-border text-xs font-medium text-zinc-300 hover:text-white transition-all cursor-pointer"
		>
			<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
			<span>Rafraîchir ScoDoc</span>
		</button>
	</div>

	{#if isLoading && !gradesData}
		<div class="space-y-6">
			<!-- 3 Top KPIs Skeletons -->
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
				{#each Array(3) as _}
					<Card class="p-4 space-y-3">
						<Skeleton class="h-3 w-28" />
						<div class="flex items-baseline gap-2">
							<Skeleton class="h-8 w-24" />
							<Skeleton class="h-4 w-8" />
						</div>
						<Skeleton class="h-3 w-36" />
					</Card>
				{/each}
			</div>

			<!-- Synthèse des UEs Skeleton -->
			<Card class="p-5 space-y-4">
				<div class="flex items-center justify-between">
					<div class="space-y-1.5">
						<Skeleton class="h-4 w-44" />
						<Skeleton class="h-3 w-56" />
					</div>
					<Skeleton class="h-4 w-28 rounded-full" />
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each Array(6) as _}
						<div class="p-3.5 rounded-xl border border-app-border bg-app-surface/50 space-y-3">
							<div class="flex items-start justify-between">
								<Skeleton class="h-4 w-32" />
								<Skeleton class="h-5 w-12 rounded-full" />
							</div>
							<Skeleton class="h-2 w-full rounded-full" />
							<div class="flex justify-between">
								<Skeleton class="h-2.5 w-16" />
								<Skeleton class="h-2.5 w-16" />
							</div>
						</div>
					{/each}
				</div>
			</Card>

			<!-- Grille des matières Skeleton -->
			<Card class="p-5 space-y-4">
				<div class="space-y-1.5">
					<Skeleton class="h-4 w-40" />
					<Skeleton class="h-3 w-64" />
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each Array(6) as _}
						<div class="p-3 rounded-lg border border-app-border bg-app-surface/40 space-y-2">
							<div class="flex justify-between items-center">
								<Skeleton class="h-3.5 w-28" />
								<Skeleton class="h-5 w-12 rounded-full" />
							</div>
							<Skeleton class="h-3 w-20" />
						</div>
					{/each}
				</div>
			</Card>

			<!-- Tableau des évaluations Skeleton -->
			<Card class="p-5 space-y-4">
				<div class="space-y-1.5">
					<Skeleton class="h-4 w-48" />
					<Skeleton class="h-3 w-52" />
				</div>
				<div class="border border-app-border rounded-lg overflow-hidden divide-y divide-white/5">
					{#each Array(5) as _}
						<div class="p-3.5 flex items-center justify-between bg-app-surface/30">
							<div class="flex items-center gap-3">
								<Skeleton class="h-5 w-14 rounded-full" />
								<div class="space-y-1.5">
									<Skeleton class="h-3.5 w-40" />
									<Skeleton class="h-2.5 w-24" />
								</div>
							</div>
							<div class="flex items-center gap-4">
								<Skeleton class="h-3 w-16" />
								<Skeleton class="h-6 w-14 rounded-full" />
							</div>
						</div>
					{/each}
				</div>
			</Card>
		</div>
	{:else if error}
		<div class="p-4 rounded-lg bg-rose-900/40 text-rose-300 text-xs font-medium">
			{error}
		</div>
	{:else if gradesData}
		<!-- 1. Top KPIs Majeurs (Sans icônes, chiffres en blanc) -->
		<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
			<!-- Carte 1 : Moyenne Générale -->
			<Card class="p-4 space-y-2">
				<span class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">Moyenne Générale</span>
				<div class="flex items-baseline gap-1.5">
					<span class="text-2xl sm:text-3xl font-black text-white">
						{formatGrade(gradesData.stats?.moyenne_generale)}
					</span>
					<span class="text-xs text-zinc-500 font-semibold">/ 20</span>
				</div>
				<div class="pt-1.5 border-t border-app-border flex items-center justify-between text-[11px] text-zinc-400">
					<span>Min <strong class="text-white font-medium">{formatGrade(gradesData.stats?.min_promo)}</strong></span>
					<span>Moy <strong class="text-white font-medium">{formatGrade(gradesData.stats?.moy_promo)}</strong></span>
					<span>Max <strong class="text-white font-medium">{formatGrade(gradesData.stats?.max_promo)}</strong></span>
				</div>
			</Card>

			<!-- Carte 2 : Rang dans la Promo (sans "Position officielle", chiffres en blanc) -->
			<Card class="p-4 space-y-2">
				<span class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">Classement Promo</span>
				<div class="flex items-baseline gap-2">
					<span class="text-2xl sm:text-3xl font-black text-white">
						{gradesData.stats?.rang || "--"}
					</span>
					<span class="text-xs text-zinc-400 font-medium">/ <span class="text-white">{gradesData.stats?.total_promo || "--"}</span> étudiants</span>
				</div>
				<div class="pt-1.5 border-t border-app-border text-[11px] text-zinc-400">
					{#if gradesData.stats?.rang && gradesData.stats?.total_promo}
						{@const pct = Math.round((gradesData.stats.rang / gradesData.stats.total_promo) * 100)}
						<span>Top <strong class="text-white font-medium">{pct}%</strong> de la promotion</span>
					{:else}
						<span>En attente de clôture</span>
					{/if}
				</div>
			</Card>

			<!-- Carte 3 : Crédits ECTS (chiffres en blanc) -->
			<Card class="p-4 space-y-2">
				<span class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">Crédits ECTS</span>
				<div class="flex items-baseline gap-1.5">
					<span class="text-2xl sm:text-3xl font-black text-white">
						{ectsAcquis()}
					</span>
					<span class="text-xs text-zinc-400 font-medium">/ <span class="text-white">{ectsTotal()}</span> ECTS</span>
				</div>
				<div class="pt-1.5 border-t border-app-border text-[11px] text-zinc-400">
					<span>Total requis pour l'année : <span class="text-white">60</span> ECTS</span>
				</div>
			</Card>
		</div>

		<!-- 2. Section des UEs (jauge ultra-fine sans bordure, chiffres en blanc) -->
		<div>
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">
					Unités d'Enseignement (UE) du Semestre
				</h2>
				<span class="text-[11px] text-zinc-500">
					Survolez la jauge pour voir la plage promo
				</span>
			</div>

			<!-- 3 UEs Principales -->
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				{#each mainUes() as ue}
					{@const userGradeNum = ue.moyenne !== null && ue.moyenne !== undefined ? (typeof ue.moyenne === 'number' ? ue.moyenne : parseFloat(ue.moyenne)) : null}
					{@const minPromoNum = ue.min_promo !== null && ue.min_promo !== undefined ? (typeof ue.min_promo === 'number' ? ue.min_promo : parseFloat(ue.min_promo)) : (userGradeNum ? Math.max(0, userGradeNum - 4.5) : 4.0)}
					{@const maxPromoNum = ue.max_promo !== null && ue.max_promo !== undefined ? (typeof ue.max_promo === 'number' ? ue.max_promo : parseFloat(ue.max_promo)) : (userGradeNum ? Math.min(20, userGradeNum + 4.5) : 17.5)}
					{@const moyPromoNum = ue.moy_promo !== null && ue.moy_promo !== undefined ? (typeof ue.moy_promo === 'number' ? ue.moy_promo : parseFloat(ue.moy_promo)) : ((minPromoNum + maxPromoNum) / 2)}
					
					{@const minPos = Math.max(0, Math.min(100, (minPromoNum / 20) * 100))}
					{@const maxPos = Math.max(0, Math.min(100, (maxPromoNum / 20) * 100))}
					{@const rangeW = Math.max(2, maxPos - minPos)}
					{@const userPos = userGradeNum !== null && !isNaN(userGradeNum) ? Math.max(0, Math.min(100, (userGradeNum / 20) * 100)) : null}
					{@const moyPromoPos = Math.max(0, Math.min(100, (moyPromoNum / 20) * 100))}

					<Card class="p-4 space-y-3">
						<div class="flex items-center gap-2">
							<span class="text-xs font-bold text-white bg-cyan-600 px-2.5 py-0.5 rounded-full shrink-0">
								{ue.code}
							</span>
							<h3 class="font-semibold text-xs text-white truncate" title={ue.titre}>
								{ue.titre}
							</h3>
						</div>

						<div class="flex items-baseline justify-between pt-0.5">
							<div class="flex items-baseline gap-1">
								<span class="text-2xl font-bold text-white">
									{formatGrade(ue.moyenne)}
								</span>
								<span class="text-xs text-zinc-500">/ 20</span>
							</div>
							<div class="text-xs text-zinc-400">
								Rang : <strong class="text-white font-semibold">{ue.rang || "--"}</strong> / <span class="text-white">{ue.total_promo || "--"}</span>
							</div>
						</div>

						<!-- Jauge ultra-fine (h-1, pas de bordure, pas de labels fixes) -->
						<div
							class="pt-1 cursor-help"
							title="Promotion : Min {formatGrade(ue.min_promo)} | Moy {formatGrade(ue.moy_promo)} | Max {formatGrade(ue.max_promo)} — Votre note : {formatGrade(ue.moyenne)}"
						>
							<div class="w-full bg-zinc-800 rounded-full h-1 relative overflow-visible flex items-center">
								<!-- Plage couverte par la promo (du minimum au maximum) -->
								<div
									class="h-full rounded-full bg-cyan-600 absolute transition-all"
									style="left: {minPos}%; width: {rangeW}%;"
								></div>

								<!-- Marqueur Moyenne Promo -->
								<div
									class="w-0.5 h-2.5 bg-cyan-300 absolute -top-0.75 z-10 pointer-events-none -translate-x-1/2"
									style="left: {moyPromoPos}%;"
								></div>

								<!-- Curseur utilisateur -->
								{#if userPos !== null}
									<div
										class="absolute -top-1 -translate-x-1/2 z-20 flex flex-col items-center pointer-events-none"
										style="left: {userPos}%;"
									>
										<div class="w-3 h-3 rounded-full bg-white shadow-xs"></div>
									</div>
								{/if}
							</div>
						</div>
					</Card>
				{/each}
			</div>

			<!-- Bandeau compact pour l'UE Bonus si existante -->
			{#if bonusUes().length > 0}
				<div class="pt-2 flex flex-wrap items-center gap-2">
					{#each bonusUes() as bUe}
						<div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-app-card text-xs text-zinc-400">
							<span class="font-bold text-white">{bUe.code}</span>
							<span>{bUe.titre}</span>
							<span class="text-zinc-600">•</span>
							<span class="text-white font-medium">{bUe.moyenne ? `${formatGrade(bUe.moyenne)}/20` : 'Non notée'}</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- 3. Grille des Moyennes par Matière (Sans bouton toggle, chiffres en blanc) -->
		<div class="space-y-3">
			<div class="flex items-center justify-between">
				<h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">
					Moyennes par Matière (Ressources & SAÉ)
				</h2>
			</div>

			<!-- Grille aérée des matières notées uniquement -->
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
				{#each gradedMatieres() as mat}
					{@const isSelected = selectedMatiere === mat.code}
					<button
						type="button"
						onclick={() => (selectedMatiere = isSelected ? "ALL" : mat.code)}
						class="text-left p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 {isSelected
							? 'border-cyan-500 bg-zinc-800 text-white'
							: 'border-app-border bg-app-card hover:border-zinc-700'}"
					>
						<div class="space-y-1 min-w-0 flex-1">
							<div class="flex items-center gap-2">
								<span class="font-bold text-xs {isSelected ? 'text-cyan-300' : 'text-white'}">
									{mat.code}
								</span>
								<span class="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 font-medium">
									{mat.evaluations_count} éval.
								</span>
							</div>
							<div class="text-xs text-zinc-400 truncate" title={mat.titre}>
								{mat.titre}
							</div>
						</div>

						<div class="text-right shrink-0">
							<div class="text-base sm:text-lg font-bold text-white">
								{mat.moyenne !== null && mat.moyenne !== undefined ? formatGrade(mat.moyenne) : "--"}
							</div>
							{#if mat.moyenne !== null && mat.moyenne !== undefined}
								<span class="text-[10px] text-zinc-500">/ 20</span>
							{/if}
						</div>
					</button>
				{/each}
			</div>

			<!-- Matières non notées minimisées sous forme de badges compacts -->
			{#if ungradedMatieres().length > 0}
				<div class="pt-1.5 flex flex-wrap items-center gap-1.5">
					<span class="text-xs text-zinc-400 mr-1">En attente de notation :</span>
					{#each ungradedMatieres() as mat}
						<button
							type="button"
							onclick={() => (selectedMatiere = selectedMatiere === mat.code ? "ALL" : mat.code)}
							class="px-2.5 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer {selectedMatiere === mat.code ? 'bg-cyan-600 text-white' : 'bg-zinc-800 text-zinc-300 hover:text-white hover:bg-zinc-700'}"
							title="{mat.code} - {mat.titre} (0 évaluation)"
						>
							{mat.code}
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- 4. Tableau épuré des Évaluations Saisies (Chiffres en blanc, badge neutre) -->
		<Card class="p-0 overflow-hidden space-y-0">
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 border-b border-app-border">
				<div>
					<h2 class="text-sm font-bold text-white">Détail des Évaluations Saisies</h2>
					<p class="text-xs text-zinc-500 mt-0.5">
						{#if selectedMatiere !== "ALL"}
							Filtré pour la matière <strong class="text-cyan-400">{selectedMatiere}</strong>
						{:else}
							Cliquez sur une évaluation pour ouvrir sa répartition promo
						{/if}
					</p>
				</div>

				<div class="flex items-center gap-2">
					<Filter class="w-3.5 h-3.5 text-zinc-500" />
					<select
						bind:value={selectedMatiere}
						class="rounded-lg border border-app-border bg-app-surface px-3 py-1.5 text-xs text-zinc-200 focus:border-cyan-500 focus:outline-none"
					>
						<option value="ALL">Toutes les matières ({allEvaluations().length} notes)</option>
						{#each gradesData.matieres || [] as mat}
							<option value={mat.code}>{mat.code} - {mat.titre} ({mat.evaluations_count})</option>
						{/each}
					</select>
				</div>
			</div>

			<!-- Tableau avec colonnes : Évaluation, Coefficient, Note, Date -->
			<div class="overflow-x-auto">
				<table class="w-full text-left text-xs">
					<thead>
						<tr class="border-b border-app-border text-zinc-400 font-semibold uppercase text-[11px] tracking-wider bg-app-surface">
							<th class="py-3 px-4">Évaluation</th>
							<th class="py-3 px-4 w-28 text-center">Coefficient</th>
							<th class="py-3 px-4 w-32 text-center">Note</th>
							<th class="py-3 px-4 w-32 text-right">Date</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-white/5">
						{#if filteredEvaluations().length === 0}
							<tr>
								<td colspan="4" class="py-10 text-center text-zinc-500 text-xs">
									Aucune note enregistrée pour cette sélection.
								</td>
							</tr>
						{:else}
							{#each filteredEvaluations() as ev}
								<tr
									onclick={() => openEvaluationDetail(ev)}
									class="hover:bg-zinc-800/60 transition-colors cursor-pointer group"
								>
									<td class="py-3 px-4">
										<div class="flex items-center gap-2.5">
											<span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-cyan-600 text-white shrink-0">
												{ev.code_matiere}
											</span>
											<div class="min-w-0">
												<div class="font-semibold text-zinc-200 group-hover:text-cyan-400 transition-colors truncate">
													{ev.description || "Évaluation"}
												</div>
												<div class="text-[11px] text-zinc-500 truncate">
													{ev.titre_matiere}
												</div>
											</div>
										</div>
									</td>
									<td class="py-3 px-4 text-center font-medium text-white">
										{ev.coefficient}
									</td>
									<td class="py-3 px-4 text-center">
										<span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-zinc-800 text-white">
											{formatGrade(ev.note)} / 20
										</span>
									</td>
									<td class="py-3 px-4 text-right text-zinc-400">
										{formatDateFr(ev.date) || "--"}
									</td>
								</tr>
							{/each}
						{/if}
					</tbody>
				</table>
			</div>
		</Card>
	{/if}
</div>

<!-- Modal d'analyse et diagramme de repartition de la note -->
<EvaluationDetailModal
	bind:open={detailModalOpen}
	evaluation={selectedEvaluation}
	totalPromo={gradesData?.stats?.total_promo || 65}
/>
