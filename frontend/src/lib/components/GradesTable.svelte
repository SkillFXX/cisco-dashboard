<script lang="ts">
	import { formatGrade, formatDateFr } from "$lib/utils";

	let {
		rows,
		showCoef = false,
		onSelect,
		emptyText = "Aucune note enregistrée."
	}: {
		rows: any[];
		showCoef?: boolean;
		onSelect?: (row: any) => void;
		emptyText?: string;
	} = $props();

	function numeric(n: any): number | null {
		const v = typeof n === "number" ? n : parseFloat(n);
		return Number.isFinite(v) ? v : null;
	}
</script>

<div class="overflow-x-auto">
	<table class="w-full text-left text-xs">
		<thead>
			<tr class="border-b border-app-border text-subtle font-medium text-[11px]">
				<th class="py-2.5 pr-4 font-medium">Évaluation</th>
				{#if showCoef}<th class="py-2.5 px-4 w-20 text-center font-medium">Coef.</th>{/if}
				<th class="py-2.5 px-4 w-28 text-right font-medium hidden sm:table-cell">Date</th>
				<th class="py-2.5 pl-4 w-24 text-right font-medium">Note</th>
			</tr>
		</thead>
		<tbody class="divide-y divide-app-border">
			{#if rows.length === 0}
				<tr><td colspan={showCoef ? 4 : 3} class="py-10 text-center text-subtle">{emptyText}</td></tr>
			{:else}
				{#each rows as row}
					{@const note = numeric(row.note)}
					<tr
						onclick={() => onSelect?.(row)}
						class="transition-colors {onSelect ? 'cursor-pointer hover:bg-app-hover' : ''}"
					>
						<td class="py-3 pr-4 min-w-0">
							<div class="font-semibold text-fg truncate">{row.description || row.type || "Évaluation"}</div>
							<div class="text-[11px] text-muted truncate">
								{[row.code_matiere, row.titre_matiere || row.matiere_nom || row.matiere].filter(Boolean).join(" · ")}
							</div>
						</td>
						{#if showCoef}
							<td class="py-3 px-4 text-center text-muted">{row.coefficient ?? "--"}</td>
						{/if}
						<td class="py-3 px-4 text-right text-muted hidden sm:table-cell">{row.date ? formatDateFr(row.date) : "--"}</td>
						<td class="py-3 pl-4 text-right whitespace-nowrap">
							<span class="text-sm font-bold tabular-nums {note !== null && note < 10 ? 'text-rose-400' : 'text-fg'}">{formatGrade(row.note)}</span>
							<span class="text-[10px] text-subtle"> / 20</span>
						</td>
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>
