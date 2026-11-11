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
	// Index de la barre qui représente l'utilisateur (la plus proche de sa note)
	let userIndex = $derived.by(() => {
		if (userNote === null || sorted.length === 0) return null;
		let best = 0;
		for (let i = 0; i < sorted.length; i++) {
			if (Math.abs(sorted[i] - userNote) < Math.abs(sorted[best] - userNote)) best = i;
		}
		return best;
	});

	// Géométrie du graphique
	const W = 640;
	const H = 230;
	const PAD = { top: 26, right: 12, bottom: 22, left: 28 };
	const plotW = W - PAD.left - PAD.right;
	const plotH = H - PAD.top - PAD.bottom;
	const y = (v: number) => PAD.top + plotH * (1 - Math.min(Math.max(v, 0), 20) / 20);
	let slot = $derived(sorted.length > 0 ? plotW / sorted.length : plotW);
	let barW = $derived(Math.max(2, slot * 0.72));
	const x = (i: number) => PAD.left + slot * i + (slot - barW) / 2;

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

	let tip = $derived(hovered === null ? null : { rank: hovered + 1, note: sorted[hovered] });
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
						<span class="text-3xl font-black text-fg tabular-nums {userNote !== null && userNote < 10 ? 'text-rose-400' : ''}">{fmt(userNote)}</span>
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
						<span class="font-semibold text-muted">Notes de la promotion, classées</span>
						{#if tip}
							<span class="text-fg font-medium tabular-nums">{tip.rank}<sup>{tip.rank === 1 ? "er" : "e"}</sup> · {fmt(tip.note)}</span>
						{/if}
					</div>

					<svg viewBox="0 0 {W} {H}" class="w-full h-auto" role="img" aria-label="Chaque barre est la note d'un étudiant, de la meilleure à la plus basse">
						{#each [0, 5, 10, 15, 20] as t}
							<line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} stroke="currentColor" class="text-fg/10" stroke-dasharray={t === 10 ? "4 4" : undefined} />
							<text x={PAD.left - 6} y={y(t) + 4} text-anchor="end" class="fill-subtle" font-size="11">{t}</text>
						{/each}

						{#each sorted as note, i}
							{@const isUser = i === userIndex}
							<rect
								x={x(i)}
								y={y(note)}
								width={barW}
								height={Math.max(1, y(0) - y(note))}
								rx={Math.min(3, barW / 2)}
								class={isUser ? "fill-cyan-500" : hovered === i ? "fill-fg/45" : "fill-fg/20"}
							/>
						{/each}

						{#if stats.moy !== null}
							<line x1={PAD.left} x2={W - PAD.right} y1={y(stats.moy)} y2={y(stats.moy)} stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="5 4" />
							<text x={W - PAD.right} y={y(stats.moy) - 5} text-anchor="end" font-size="11" fill="#f59e0b" font-weight="600">Moy. {fmt(stats.moy)}</text>
						{/if}

						{#if userIndex !== null && userNote !== null}
							<text x={x(userIndex) + barW / 2} y={y(sorted[userIndex]) - 7} text-anchor="middle" font-size="11" font-weight="700" class="fill-cyan-500">Vous</text>
						{/if}

						{#each sorted as _, i}
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

						<text x={PAD.left} y={H - 5} font-size="11" class="fill-subtle">1<tspan baseline-shift="super" font-size="8">er</tspan></text>
						<text x={W - PAD.right} y={H - 5} text-anchor="end" font-size="11" class="fill-subtle">{sorted.length}<tspan baseline-shift="super" font-size="8">e</tspan></text>
					</svg>

					{#if distData?.estimated}
						<p class="text-[11px] text-amber-400 mt-1">
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
