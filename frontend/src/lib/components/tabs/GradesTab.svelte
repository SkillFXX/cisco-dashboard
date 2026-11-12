<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { Filter, RefreshCw } from "lucide-svelte";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import EvaluationDetailModal from "../EvaluationDetailModal.svelte";
	import GradeHistoryChart from "../GradeHistoryChart.svelte";
	import Sparkline from "../Sparkline.svelte";
	import AverageCard from "../AverageCard.svelte";
	import GradesTable from "../GradesTable.svelte";
	import Modal from "../Modal.svelte";

	let gradesData = $state<any>(null);
	let history = $state<any[]>([]);
	let historyMetric = $state<"moyenne" | "rang" | null>(null);
	let historyOpen = $state(false);

	// Séries pour les mini-courbes (au moins 2 points pour tracer)
	let moyenneSeries = $derived(history.filter((h) => h.moyenne != null).map((h) => h.moyenne as number));
	let rangSeries = $derived(history.filter((h) => h.rang != null).map((h) => h.rang as number));

	function openHistory(metric: "moyenne" | "rang") {
		historyMetric = metric;
		historyOpen = true;
	}
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
			// Chargé après les notes : le point du jour est enregistré lors de la récupération ScoDoc
			history = await api.getGradeHistory().catch(() => []);
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
			<h1 class="text-xl font-bold text-fg tracking-tight">
				Notes
			</h1>
		</div>

		<button
			onclick={() => loadGrades(true)}
			disabled={isLoading}
			class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-app-card hover:bg-app-raised border border-app-border text-xs font-medium text-muted hover:text-fg transition-all cursor-pointer"
		>
			<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
			<span>Actualiser</span>
		</button>
	</div>

	{#if isLoading && !gradesData}
		<div class="space-y-6">
			<!-- 3 Top KPIs Skeletons -->
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
				{#each Array(3) as _}
					<Card class="p-4 space-y-3">
						<Skeleton class="h-3 w-28" />
						<div class="relative flex items-baseline gap-2">
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
						<div class="space-y-3">
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
						<div class="space-y-2">
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
				<div class="border border-app-border rounded-lg overflow-hidden divide-y divide-app-border">
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
			<AverageCard stats={gradesData.stats} series={moyenneSeries} onclick={moyenneSeries.length > 1 ? () => openHistory("moyenne") : undefined} />

			<!-- Carte 2 : Rang dans la Promo -->
			<Card
				class="p-4 space-y-2 relative overflow-hidden {rangSeries.length > 1 ? 'cursor-pointer hover:border-app-border group' : ''}"
				role={rangSeries.length > 1 ? "button" : undefined}
				tabindex={rangSeries.length > 1 ? 0 : undefined}
				aria-label={rangSeries.length > 1 ? "Voir l'évolution du classement" : undefined}
				onclick={() => rangSeries.length > 1 && openHistory("rang")}
				onkeydown={(e: KeyboardEvent) => e.key === "Enter" && rangSeries.length > 1 && openHistory("rang")}
			>
				{#if rangSeries.length > 1}
					<div class="absolute top-3 right-3 bottom-12 w-[52%] pointer-events-none">
						<Sparkline values={rangSeries} invert color="#7c5cd6" />
					</div>
				{/if}
				<span class="relative text-[11px] font-semibold uppercase tracking-wider text-muted">Classement Promo</span>
				<div class="relative flex items-baseline gap-2">
					<span class="text-2xl sm:text-3xl font-black text-fg">
						{gradesData.stats?.rang || "--"}
					</span>
					<span class="text-xs text-muted font-medium">/ <span class="text-fg">{gradesData.stats?.total_promo || "--"}</span> étudiants</span>
				</div>
				<div class="pt-1.5 border-t border-app-border text-[11px] text-muted">
					{#if gradesData.stats?.rang && gradesData.stats?.total_promo}
						{@const pct = Math.round((gradesData.stats.rang / gradesData.stats.total_promo) * 100)}
						<span>Top <strong class="text-fg font-medium">{pct}%</strong> de la promotion</span>
					{:else}
						<span>En attente de clôture</span>
					{/if}
				</div>
			</Card>

			<!-- Carte 3 : Crédits ECTS (chiffres en blanc) -->
			<Card class="p-4 space-y-2">
				<span class="text-[11px] font-semibold uppercase tracking-wider text-muted">Crédits ECTS</span>
				<div class="relative flex items-baseline gap-1.5">
					<span class="text-2xl sm:text-3xl font-black text-fg">
						{ectsAcquis()}
					</span>
					<span class="text-xs text-muted font-medium">/ <span class="text-fg">{ectsTotal()}</span> ECTS</span>
				</div>
			</Card>
		</div>

		<!-- 2. Section des UEs (jauge ultra-fine sans bordure, chiffres en blanc) -->
		<div>
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-xs font-semibold uppercase tracking-wider text-muted">
					Unités d'Enseignement (UE) du Semestre
				</h2>
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
							<span class="text-[11px] font-bold text-muted shrink-0">
								{ue.code}
							</span>
							<h3 class="font-semibold text-xs text-fg truncate" title={ue.titre}>
								{ue.titre}
							</h3>
						</div>

						<div class="flex items-baseline justify-between pt-0.5">
							<div class="flex items-baseline gap-1">
								<span class="text-2xl font-bold text-fg">
									{formatGrade(ue.moyenne)}
								</span>
								<span class="text-xs text-subtle">/ 20</span>
							</div>
							<div class="text-xs text-muted">
								Rang : <strong class="text-fg font-semibold">{ue.rang || "--"}</strong> / <span class="text-fg">{ue.total_promo || "--"}</span>
							</div>
						</div>

						<!-- Jauge ultra-fine (h-1, pas de bordure, pas de labels fixes) -->
						<div
							class="pt-1 cursor-help"
							title="Promotion : Min {formatGrade(ue.min_promo)} | Moy {formatGrade(ue.moy_promo)} | Max {formatGrade(ue.max_promo)} — Votre note : {formatGrade(ue.moyenne)}"
						>
							<div class="w-full bg-app-raised rounded-full h-1 relative overflow-visible flex items-center">
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
										<div class="w-3 h-3 rounded-full bg-fg shadow-xs"></div>
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
						<div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-app-card text-xs text-muted">
							<span class="font-bold text-fg">{bUe.code}</span>
							<span>{bUe.titre}</span>
							<span class="text-subtle">•</span>
							<span class="text-fg font-medium">{bUe.moyenne ? `${formatGrade(bUe.moyenne)}/20` : 'Non notée'}</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- 3. Grille des Moyennes par Matière (Sans bouton toggle, chiffres en blanc) -->
		<div class="space-y-3">
			<div class="flex items-center justify-between">
				<h2 class="text-xs font-semibold uppercase tracking-wider text-muted">
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
							? 'border-cyan-500 bg-app-raised text-fg'
							: 'border-app-border bg-app-card hover:border-app-border'}"
					>
						<div class="space-y-1 min-w-0 flex-1">
							<div class="flex items-center gap-2">
								<span class="font-bold text-xs {isSelected ? 'text-fg' : 'text-fg'}">
									{mat.code}
								</span>
								<span class="text-[10px] px-2 py-0.5 rounded-full bg-app-raised text-muted font-medium">
									{mat.evaluations_count} éval.
								</span>
							</div>
							<div class="text-xs text-muted truncate" title={mat.titre}>
								{mat.titre}
							</div>
						</div>

						<div class="text-right shrink-0">
							<div class="text-base sm:text-lg font-bold text-fg">
								{mat.moyenne !== null && mat.moyenne !== undefined ? formatGrade(mat.moyenne) : "--"}
							</div>
							{#if mat.moyenne !== null && mat.moyenne !== undefined}
								<span class="text-[10px] text-subtle">/ 20</span>
							{/if}
						</div>
					</button>
				{/each}
			</div>

			<!-- Matières non notées minimisées sous forme de badges compacts -->
			{#if ungradedMatieres().length > 0}
				<div class="pt-1.5 flex flex-wrap items-center gap-1.5">
					<span class="text-xs text-muted mr-1">En attente de notation :</span>
					{#each ungradedMatieres() as mat}
						<button
							type="button"
							onclick={() => (selectedMatiere = selectedMatiere === mat.code ? "ALL" : mat.code)}
							class="px-2.5 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer {selectedMatiere === mat.code ? 'bg-cyan-600 text-white' : 'bg-app-raised text-muted hover:text-white hover:bg-app-raised2'}"
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
					<h2 class="text-sm font-bold text-fg">Détail des Évaluations Saisies</h2>
					<p class="text-xs text-subtle mt-0.5">
						{#if selectedMatiere !== "ALL"}
							Filtré pour la matière <strong class="text-fg">{selectedMatiere}</strong>
						{:else}
							Détail et répartition promo au clic
						{/if}
					</p>
				</div>

				<div class="flex items-center gap-2">
					<Filter class="w-3.5 h-3.5 text-subtle" />
					<select
						bind:value={selectedMatiere}
						class="rounded-lg border border-app-border bg-app-surface px-3 py-1.5 text-xs text-fg focus:border-cyan-500 focus:outline-none"
					>
						<option value="ALL">Toutes les matières ({allEvaluations().length} notes)</option>
						{#each gradesData.matieres || [] as mat}
							<option value={mat.code}>{mat.code} - {mat.titre} ({mat.evaluations_count})</option>
						{/each}
					</select>
				</div>
			</div>

			<div class="px-4 pb-2">
				<GradesTable rows={filteredEvaluations()} showCoef onSelect={openEvaluationDetail} emptyText="Aucune note enregistrée pour cette sélection." />
			</div>
		</Card>
	{/if}
</div>

<!-- Évolution détaillée de la moyenne ou du rang -->
<Modal
	bind:open={historyOpen}
	title={historyMetric === "rang" ? "Évolution du classement" : "Évolution de la moyenne générale"}
	description="Un point par jour de connexion. Survolez la courbe pour voir chaque relevé."
	class="max-w-2xl"
>
	{#if historyMetric}
		<GradeHistoryChart data={history} metric={historyMetric} />
	{/if}
</Modal>

<!-- Modal d'analyse et diagramme de repartition de la note -->
<EvaluationDetailModal
	bind:open={detailModalOpen}
	evaluation={selectedEvaluation}
	totalPromo={gradesData?.stats?.total_promo || 65}
/>
