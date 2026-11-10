<script lang="ts">
	import { Sun, Moon, SunMoon } from "lucide-svelte";
	import { theme, type ThemeMode } from "$lib/stores/theme.svelte";

	const OPTIONS: { mode: ThemeMode; label: string; icon: typeof Sun }[] = [
		{ mode: "auto", label: "Automatique", icon: SunMoon },
		{ mode: "light", label: "Clair", icon: Sun },
		{ mode: "dark", label: "Sombre", icon: Moon }
	];
</script>

<div class="inline-flex rounded-lg bg-app-raised p-0.5" role="radiogroup" aria-label="Thème de l'interface">
	{#each OPTIONS as opt}
		{@const Icon = opt.icon}
		<button
			type="button"
			role="radio"
			aria-checked={theme.mode === opt.mode}
			onclick={() => theme.set(opt.mode)}
			class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium cursor-pointer transition-colors {theme.mode === opt.mode ? 'bg-app-card text-fg shadow-xs' : 'text-muted hover:text-fg'}"
		>
			<Icon class="w-3.5 h-3.5" />
			<span>{opt.label}</span>
		</button>
	{/each}
</div>
