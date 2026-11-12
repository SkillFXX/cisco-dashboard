<script lang="ts">
	import Modal from "./Modal.svelte";
	import { api } from "$lib/api";
	import { formatDateFr } from "$lib/utils";
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

	let isLoading = $state(false);
	let distData = $state<any>(null);
	let error = $state("");
	let hovered = $state<number | null>(null);

	function toNum(v: any): number | null {
		if (v === null || v === undefined) return null;
		const n = typeof v === "number" ? v : parseFloat(v);
		return Number.isFinite(n) ? n : null;
	}
	const fmt = (v: number | null) => (v === null ? "--" : v.toFixed(2).replace(".", ","));

	let userNote = $derived(toNum(evaluation?.note));

	// Toutes les notes de la promo, de la meilleure à la plus basse (une barre par étudiant)
	let sorted = $derived<number[]>([...(distData?.distribution ?? [])].sort((a, b) => b - a));
	let stats = $derived({
		min: toNum(evaluation?.min_promo ?? distData?.min_promo),
		moy: toNum(evaluation?.moy_promo ?? distData?.moy_promo),
		max: toNum(evaluation?.max_promo ?? distData?.max_promo)
	});
	let userRank = $derived(userNote === null || sorted.length === 0 || distData?.estimated ? null : 1 + sorted.filter((n) => n > userNote + 1e-9).length);
	// Répartition par note : un intervalle d'un point (0–1, 1–2, … 19–20 ; le 20 est compté dans le dernier)
	const BINS = 20;
	let bins = $derived.by(() => {
		const counts = Array<number>(BINS).fill(0);
		for (const n of sorted) counts[Math.min(BINS - 1, Math.max(0, Math.floor(n)))]++;
		return counts;
	});
	let maxCount = $derived(Math.max(1, ...bins));
	let userBin = $derived(userNote === null ? null : Math.min(BINS - 1, Math.max(0, Math.floor(userNote))));

	// Géométrie du graphique
	const W = 640;
	const H = 230;
	const PAD = { top: 28, right: 12, bottom: 24, left: 28 };
	const plotW = W - PAD.left - PAD.right;
	const plotH = H - PAD.top - PAD.bottom;
	const slot = plotW / BINS;
	const barW = slot * 0.78;
	const xNote = (v: number) => PAD.left + (Math.min(Math.max(v, 0), 20) / 20) * plotW;
	const yCount = (c: number) => PAD.top + plotH * (1 - c / maxCount);
	let yTicks = $derived(Array.from(new Set([0, Math.ceil(maxCount / 2), maxCount])));

	$effect(() => {
		if (open && evaluation?.id) {
			load(evaluation);
		} else if (!open) {
			distData = null;
			error = "";
			hovered = null;
		}
	});

	async function load(ev: any) {
		isLoading = true;
		error = "";
		try {
			distData = await api.getEvaluationDistribution(ev.id, {
				min_promo: ev.min_promo,
				moy_promo: ev.moy_promo,
				max_promo: ev.max_promo,
				total_promo: totalPromo
			});
		} catch (e: any) {
			error = e.message || "Impossible de charger la répartition.";
		} finally {
			isLoading = false;
		}
	}

	let tip = $derived(hovered === null ? null : { from: hovered, count: bins[hovered] });
</script>

<Modal bind:open title="" class="max-w-2xl">
	{#if evaluation}
		<div class="space-y-5">
			<div class="flex items-start justify-between gap-4 pr-6">
				<div class="min-w-0 space-y-0.5">
					<h2 class="text-base font-bold text-fg leading-snug">{evaluation.description || "Évaluation"}</h2>
					<p class="text-xs text-muted">
						{[evaluation.code_matiere, evaluation.titre_matiere].filter(Boolean).join(" · ")}
					</p>
					<p class="text-xs text-subtle">
						Coef. {evaluation.coefficient ?? 1}{evaluation.date ? ` · ${formatDateFr(evaluation.date)}` : ""}
					</p>
				</div>
				<div class="text-right shrink-0">
					<div class="flex items-baseline justify-end gap-1">
						<span class="text-3xl font-black text-fg tabular-nums">{fmt(userNote)}</span>
						<span class="text-xs text-subtle">/ 20</span>
					</div>
					{#if userRank !== null}
						<div class="text-xs text-muted">{userRank}<sup>{userRank === 1 ? "er" : "e"}</sup> sur {sorted.length}</div>
					{/if}
				</div>
			</div>

			{#if isLoading}
				<div class="py-14 flex flex-col items-center justify-center text-muted text-xs gap-2">
					<RefreshCw class="w-5 h-5 animate-spin text-cyan-400" />
					<span>Chargement des notes de la promotion…</span>
				</div>
			{:else if error && sorted.length === 0}
				<p class="text-xs text-rose-400">{error}</p>
			{:else if sorted.length > 0}
				<div>
					<div class="flex items-center justify-between h-5 text-xs mb-1">
						<span class="font-semibold text-muted">Répartition des notes de la promotion</span>
						{#if tip}
							<span class="text-fg font-medium tabular-nums">{tip.from} – {tip.from + 1} : {tip.count} étudiant{tip.count > 1 ? "s" : ""}</span>
						{/if}
					</div>

					<svg viewBox="0 0 {W} {H}" class="w-full h-auto" role="img" aria-label="Nombre d'étudiants par note, par intervalle d'un point">
						{#each yTicks as t}
							<line x1={PAD.left} x2={W - PAD.right} y1={yCount(t)} y2={yCount(t)} stroke="currentColor" class="text-fg/10" />
							<text x={PAD.left - 6} y={yCount(t) + 4} text-anchor="end" class="fill-subtle" font-size="11">{t}</text>
						{/each}

						{#each bins as count, i}
							<rect
								x={PAD.left + slot * i + (slot - barW) / 2}
								y={yCount(count)}
								width={barW}
								height={Math.max(0, yCount(0) - yCount(count))}
								rx="3"
								class={i === userBin ? "fill-cyan-500" : hovered === i ? "fill-fg/45" : "fill-fg/20"}
							/>
						{/each}

						{#if stats.moy !== null}
							<line x1={xNote(stats.moy)} x2={xNote(stats.moy)} y1={PAD.top - 6} y2={yCount(0)} stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="5 4" />
							<text x={xNote(stats.moy) + 5} y={PAD.top - 10} font-size="11" fill="#f59e0b" font-weight="600">Moy. {fmt(stats.moy)}</text>
						{/if}

						{#if userBin !== null}
							<text x={PAD.left + slot * (userBin + 0.5)} y={yCount(bins[userBin]) - 7} text-anchor="middle" font-size="11" font-weight="700" class="fill-cyan-500">Vous</text>
						{/if}

						{#each bins as _, i}
							<rect
								x={PAD.left + slot * i}
								y={PAD.top}
								width={slot}
								height={plotH}
								fill="transparent"
								role="presentation"
								onpointerenter={() => (hovered = i)}
								onpointerleave={() => (hovered = null)}
							/>
						{/each}

						{#each [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20] as t}
							<text x={xNote(t)} y={H - 6} text-anchor="middle" font-size="11" class="fill-subtle">{t}</text>
						{/each}
					</svg>

					{#if distData?.estimated}
						<p class="text-[11px] text-muted mt-1">
							Répartition estimée à partir du minimum, de la moyenne et du maximum : ScoDoc ne fournit pas les notes individuelles de cette évaluation.
						</p>
					{/if}
				</div>
			{/if}

			<div class="grid grid-cols-3 divide-x divide-app-border border-t border-app-border pt-3 text-center">
				{#each [["Minimum", stats.min], ["Moyenne", stats.moy], ["Maximum", stats.max]] as [label, value]}
					<div class="px-2">
						<div class="text-[11px] text-subtle">{label}</div>
						<div class="text-base font-bold text-fg tabular-nums">{fmt(value as number | null)}</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</Modal>
