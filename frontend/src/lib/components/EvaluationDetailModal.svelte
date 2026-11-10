<script lang="ts">
	import Modal from "./Modal.svelte";
	import { api } from "$lib/api";
	import { RefreshCw } from "lucide-svelte";

	let {
		open = $bindable(false),
		evaluation = null,
		totalPromo = 65
	}: {
		open: boolean;
		evaluation: any | null;
		totalPromo?: number;
	} = $props();

	let isLoadingDist = $state(false);
	let distData = $state<any>(null);
	let errorDist = $state("");

	interface Bin {
		label: string;
		min: number;
		max: number;
		count: number;
		percent: number;
		isUserBin: boolean;
	}

	let userNoteNum = $derived(() => {
		if (!evaluation || evaluation.note === null || evaluation.note === undefined) return null;
		const n = typeof evaluation.note === "number" ? evaluation.note : parseFloat(evaluation.note);
		return isNaN(n) ? null : n;
	});

	let moyPromoNum = $derived(() => {
		if (!evaluation) return null;
		const m = evaluation.moy_promo ?? distData?.moy_promo;
		if (m === null || m === undefined) return null;
		const num = typeof m === "number" ? m : parseFloat(m);
		return isNaN(num) ? null : num;
	});

	let minPromoNum = $derived(() => {
		if (!evaluation) return null;
		const val = evaluation.min_promo ?? distData?.min_promo;
		if (val === null || val === undefined) return null;
		const num = typeof val === "number" ? val : parseFloat(val);
		return isNaN(num) ? null : num;
	});

	let maxPromoNum = $derived(() => {
		if (!evaluation) return null;
		const val = evaluation.max_promo ?? distData?.max_promo;
		if (val === null || val === undefined) return null;
		const num = typeof val === "number" ? val : parseFloat(val);
		return isNaN(num) ? null : num;
	});

	let bins = $derived((): Bin[] => {
		const result: Bin[] = [];
		for (let i = 0; i < 10; i++) {
			const bMin = i * 2;
			const bMax = (i + 1) * 2;
			result.push({
				label: `${bMin}-${bMax}`,
				min: bMin,
				max: bMax,
				count: 0,
				percent: 0,
				isUserBin: false
			});
		}

		const notesList: number[] = distData?.distribution || [];
		if (notesList.length > 0) {
			for (const val of notesList) {
				const idx = Math.min(9, Math.max(0, Math.floor(val / 2)));
				result[idx].count++;
			}
			const total = notesList.length;
			for (const b of result) {
				b.percent = Math.round((b.count / total) * 100);
			}
		}

		const userN = userNoteNum();
		if (userN !== null) {
			const userIdx = Math.min(9, Math.max(0, Math.floor(userN / 2)));
			if (result[userIdx]) {
				result[userIdx].isUserBin = true;
			}
		}

		return result;
	});

	let maxBinCount = $derived(() => {
		const list = bins();
		const max = Math.max(...list.map((b) => b.count));
		return max > 0 ? max : 1;
	});

	$effect(() => {
		if (open && evaluation && evaluation.id) {
			loadDistribution(evaluation);
		} else if (!open) {
			distData = null;
			errorDist = "";
		}
	});

	async function loadDistribution(ev: any) {
		isLoadingDist = true;
		errorDist = "";
		try {
			const res = await api.getEvaluationDistribution(ev.id, {
				min_promo: ev.min_promo,
				moy_promo: ev.moy_promo,
				max_promo: ev.max_promo,
				total_promo: totalPromo
			});
			distData = res;
		} catch (err: any) {
			errorDist = err.message || "Impossible de charger la répartition.";
		} finally {
			isLoadingDist = false;
		}
	}

	function formatVal(v: any): string {
		if (v === null || v === undefined) return "--";
		const num = typeof v === "number" ? v : parseFloat(v);
		return isNaN(num) ? "--" : num.toFixed(2);
	}
</script>

<Modal bind:open title="" class="max-w-xl">
	{#if evaluation}
		<div class="space-y-5">
			<!-- En-tête épuré et sans boîtes imbriquées -->
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-app-border">
				<div class="space-y-1 min-w-0">
					<div class="flex items-center gap-2 flex-wrap text-xs text-muted">
						<span class="font-bold text-white bg-cyan-600 px-2.5 py-0.5 rounded-full text-xs shrink-0">
							{evaluation.code_matiere}
						</span>
						<span class="font-medium text-muted">Coef. {evaluation.coefficient ?? 1.0}</span>
						{#if evaluation.date}
							<span class="text-subtle">•</span>
							<span class="text-muted">{new Date(evaluation.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
						{/if}
					</div>
					<h2 class="text-base font-bold text-fg truncate">
						{evaluation.description || "Évaluation"}
					</h2>
					<p class="text-xs text-muted truncate">
						{evaluation.titre_matiere}
					</p>
				</div>

				<!-- Note de l'étudiant en blanc -->
				<div class="self-start sm:self-center shrink-0">
					<div class="inline-flex items-baseline gap-1.5 bg-app-raised text-fg px-4 py-1.5 rounded-full font-bold">
						<span class="text-xs text-muted uppercase font-medium">Note</span>
						<span class="text-xl sm:text-2xl font-black text-fg">{formatVal(evaluation.note)}</span>
						<span class="text-xs text-muted font-normal">/ 20</span>
					</div>
				</div>
			</div>

			<!-- Indicateurs statistiques essentiels (chiffres en blanc) -->
			<div class="grid grid-cols-4 divide-x divide-app-border py-3 bg-app-surface rounded-xl border border-app-border text-center">
				<div class="px-2">
					<span class="block text-[11px] text-muted font-medium uppercase tracking-wider">Note Min</span>
					<span class="block text-base sm:text-lg font-bold text-fg mt-0.5">{formatVal(minPromoNum())}</span>
				</div>

				<div class="px-2">
					<span class="block text-[11px] text-muted font-medium uppercase tracking-wider">Moyenne</span>
					<span class="block text-base sm:text-lg font-bold text-fg mt-0.5">{formatVal(moyPromoNum())}</span>
				</div>

				<div class="px-2">
					<span class="block text-[11px] text-muted font-medium uppercase tracking-wider">Note Max</span>
					<span class="block text-base sm:text-lg font-bold text-fg mt-0.5">{formatVal(maxPromoNum())}</span>
				</div>

				<div class="px-2">
					<span class="block text-[11px] text-muted font-medium uppercase tracking-wider">Effectif</span>
					<span class="block text-base sm:text-lg font-bold text-fg mt-0.5">{distData?.count || totalPromo}</span>
				</div>
			</div>

			<!-- Distribution des notes dans la promo -->
			<div class="space-y-3 pt-1">
				<div class="flex items-center justify-between">
					<h3 class="text-xs font-semibold text-muted uppercase tracking-wider">
						Répartition des Notes
					</h3>

					<div class="flex items-center gap-3 text-xs">
						<div class="flex items-center gap-1.5">
							<span class="w-2.5 h-2.5 rounded-full bg-cyan-500"></span>
							<span class="text-muted">Votre tranche</span>
						</div>
						<div class="flex items-center gap-1.5">
							<span class="w-2.5 h-2.5 rounded-full bg-app-raised2"></span>
							<span class="text-muted">Promotion</span>
						</div>
					</div>
				</div>

				{#if isLoadingDist}
					<div class="py-12 flex flex-col items-center justify-center text-muted text-xs gap-2">
						<RefreshCw class="w-5 h-5 animate-spin text-cyan-400" />
						<span>Chargement de la répartition...</span>
					</div>
				{:else if errorDist && (!distData || distData.distribution.length === 0)}
					<div class="p-3 rounded-lg bg-rose-900/40 text-rose-300 text-xs font-medium">
						{errorDist}
					</div>
				{:else}
					<!-- Histogramme épuré -->
					<div class="pt-2">
						<div class="h-40 flex items-end gap-1.5 sm:gap-2 px-1">
							{#each bins() as b}
								{@const maxH = maxBinCount()}
								{@const hPercent = Math.max(6, Math.round((b.count / maxH) * 100))}
								<div class="flex-1 flex flex-col items-center h-full justify-end group relative">
									<!-- Info-bulle au survol -->
									<div class="opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none absolute -top-8 bg-app-surface border border-app-border text-fg text-[10px] rounded-md px-2 py-1 shadow-md whitespace-nowrap z-20">
										<span class="font-bold">{b.min} à {b.max} : </span>
										<span>{b.count} étud. ({b.percent}%)</span>
									</div>

									<!-- Effectif au dessus de la barre (en blanc) -->
									<span class="text-[10px] text-muted group-hover:text-fg transition-colors mb-1 {b.isUserBin ? 'text-fg font-bold' : ''}">
										{b.count}
									</span>

									<!-- Barre -->
									<div
										class="w-full rounded-t-sm transition-all duration-200 {b.isUserBin
											? 'bg-cyan-500'
											: 'bg-app-raised2 hover:bg-app-raised2'}"
										style="height: {hPercent}%"
									></div>

									<!-- Tranche de notes en bas -->
									<span class="text-[9px] text-muted mt-2 whitespace-nowrap {b.isUserBin ? 'text-fg font-bold' : ''}">
										{b.label}
									</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			<!-- Bouton de fermeture sobre -->
			<div class="flex justify-end pt-2 border-t border-app-border">
				<button
					type="button"
					onclick={() => (open = false)}
					class="px-4 py-2 rounded-lg bg-app-raised hover:bg-app-raised2 text-xs font-semibold text-fg transition-all cursor-pointer"
				>
					Fermer
				</button>
			</div>
		</div>
	{/if}
</Modal>
