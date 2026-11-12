<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import Card from "../Card.svelte";
	import Modal from "../Modal.svelte";
	import Skeleton from "../Skeleton.svelte";
	import { Mail, Webhook, Plus, Trash2, Pencil, Check, X } from "lucide-svelte";

	type Rule = {
		id?: number;
		name: string;
		enabled: boolean;
		trigger: "new_grade" | "deadline" | "daily_digest" | "new_week";
		params: Record<string, any>;
		channels: string[];
	};

	const TRIGGERS = [
		{ id: "new_grade", label: "Nouvelle note", hint: "Dès qu'une nouvelle note apparaît dans ScoDoc." },
		{ id: "deadline", label: "Avant une échéance", hint: "Un rappel X heures avant un devoir, DM, TP ou DS." },
		{ id: "daily_digest", label: "Récapitulatif quotidien", hint: "Un résumé des échéances à venir, chaque jour à l'heure choisie." },
		{ id: "new_week", label: "Nouvelle semaine", hint: "L'emploi du temps de la semaine suivante, envoyé en image à la fin de chaque semaine." }
	] as const;

	const DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];

	const CATEGORIES = [
		{ id: "ds", label: "DS" },
		{ id: "dm", label: "DM" },
		{ id: "tp", label: "TP" },
		{ id: "other", label: "Autres" }
	];

	let isLoading = $state(true);
	let error = $state("");
	let notice = $state("");
	let overview = $state<any>(null);

	let editing = $state<Rule | null>(null);
	let modalOpen = $state(false);
	let isSavingRule = $state(false);

	// Fermer la fenêtre abandonne l'édition en cours
	$effect(() => {
		if (!modalOpen) editing = null;
	});

	async function load() {
		try {
			overview = await api.getNotifications();
		} catch (e: any) {
			error = e.message || "Impossible de charger les notifications.";
		} finally {
			isLoading = false;
		}
	}

	onMount(load);

	function flash(message: string) {
		notice = message;
		setTimeout(() => (notice = ""), 3500);
	}

	function newRule(): Rule {
		return {
			name: "",
			enabled: true,
			trigger: "new_grade",
			params: {},
			channels: overview?.email_available ? ["email"] : overview?.webhook_configured ? ["webhook"] : []
		};
	}

	function startNew() {
		editing = newRule();
		modalOpen = true;
	}

	function startEdit(rule: Rule) {
		editing = JSON.parse(JSON.stringify(rule));
		modalOpen = true;
	}

	function setTrigger(trigger: Rule["trigger"]) {
		if (!editing) return;
		editing.trigger = trigger;
		editing.params =
			trigger === "deadline"
				? { hours_before: 24, include_done: false, categories: [] }
				: trigger === "daily_digest"
					? { hour: 18, days_ahead: 3, include_done: false }
					: trigger === "new_week"
						? { day: 6, hour: 18 }
						: {};
		if (!editing.name) editing.name = TRIGGERS.find((t) => t.id === trigger)?.label || "";
	}

	function toggleIn(list: string[], value: string) {
		return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
	}

	async function saveRule(e: SubmitEvent) {
		e.preventDefault();
		if (!editing) return;
		if (editing.channels.length === 0) {
			error = "Choisissez au moins un canal d'envoi.";
			return;
		}
		isSavingRule = true;
		error = "";
		try {
			const payload = { ...editing };
			if (editing.id) await api.updateNotificationRule(editing.id, payload);
			else await api.createNotificationRule(payload);
			modalOpen = false;
			await load();
			flash("Notification enregistrée.");
		} catch (e: any) {
			error = e.message;
		} finally {
			isSavingRule = false;
		}
	}

	async function toggleRule(rule: Rule) {
		const next = !rule.enabled;
		rule.enabled = next; // optimiste
		try {
			await api.updateNotificationRule(rule.id!, { ...rule, enabled: next });
		} catch (e: any) {
			rule.enabled = !next;
			error = e.message;
		}
	}

	async function removeRule(rule: Rule) {
		if (!confirm(`Supprimer la notification « ${rule.name} » ?`)) return;
		try {
			await api.deleteNotificationRule(rule.id!);
			overview.rules = overview.rules.filter((r: Rule) => r.id !== rule.id);
		} catch (e: any) {
			error = e.message;
		}
	}

	function describe(rule: Rule): string {
		const p = rule.params || {};
		if (rule.trigger === "new_grade") return "À chaque nouvelle note";
		if (rule.trigger === "deadline") {
			const cats = (p.categories || []).length ? (p.categories as string[]).map((c) => c.toUpperCase()).join(", ") : "tous les types";
			const h = p.hours_before;
			const delay = h % 24 === 0 ? `${h / 24} jour${h / 24 > 1 ? "s" : ""}` : `${h} h`;
			return `${delay} avant l'échéance (${cats}) — ${p.include_done ? "faits ou non" : "non faits uniquement"}`;
		}
		if (rule.trigger === "new_week") return `${DAYS[p.day ?? 6]} à ${String(p.hour ?? 18).padStart(2, "0")}h : emploi du temps de la semaine suivante (image)`;
		return `Chaque jour à ${String(p.hour).padStart(2, "0")}h, échéances des ${p.days_ahead} prochains jours`;
	}

	const inputClass = "w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none";
</script>

<div class="space-y-6">
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-fg">Notifications</h1>
		</div>
		{#if overview}
			<button
				onclick={startNew}
				class="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold cursor-pointer"
			>
				<Plus class="w-3.5 h-3.5" />
				<span>Nouvelle notification</span>
			</button>
		{/if}
	</div>

	{#if error}
		<div class="rounded-lg bg-red-600/20 p-3 text-xs text-red-300 font-medium flex justify-between gap-2">
			<span>{error}</span>
			<button onclick={() => (error = "")} aria-label="Fermer" class="cursor-pointer"><X class="w-3.5 h-3.5" /></button>
		</div>
	{/if}
	{#if notice}
		<div class="rounded-lg bg-emerald-600/20 p-3 text-xs text-emerald-300 font-medium flex items-center gap-2">
			<Check class="w-3.5 h-3.5" />{notice}
		</div>
	{/if}

	{#if isLoading}
		<Skeleton class="h-40 w-full" />
		<Skeleton class="h-32 w-full" />
	{:else if overview}
		<!-- Liste -->
		{#if overview.rules.length === 0}
			<div class="py-10 text-center border border-dashed border-app-border rounded-xl bg-app-card/40 text-subtle text-xs">
				Aucune notification pour l'instant. Créez-en une pour être prévenu automatiquement.
			</div>
		{:else}
			<div class="border border-app-border rounded-xl bg-app-card overflow-hidden divide-y divide-app-border">
				{#each overview.rules as rule (rule.id)}
					<div class="flex items-center gap-3 p-3.5">
						<button
							onclick={() => toggleRule(rule)}
							role="switch"
							aria-checked={rule.enabled}
							aria-label="Activer {rule.name}"
							class="relative w-9 h-5 rounded-full shrink-0 transition-colors cursor-pointer {rule.enabled ? 'bg-cyan-600' : 'bg-app-raised2'}"
						>
							<span class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-fg transition-transform {rule.enabled ? 'translate-x-4' : ''}"></span>
						</button>
						<div class="min-w-0 flex-1">
							<div class="text-xs font-bold text-fg truncate">{rule.name}</div>
							<div class="text-xs text-muted truncate">{describe(rule)}</div>
						</div>
						<div class="hidden sm:flex items-center gap-1.5 text-subtle">
							{#if rule.channels.includes("email")}<Mail class="w-3.5 h-3.5" />{/if}
							{#if rule.channels.includes("webhook")}<Webhook class="w-3.5 h-3.5" />{/if}
						</div>
						<button onclick={() => startEdit(rule)} class="p-1.5 text-muted hover:text-fg cursor-pointer" aria-label="Modifier"><Pencil class="w-3.5 h-3.5" /></button>
						<button onclick={() => removeRule(rule)} class="p-1.5 text-muted hover:text-red-400 cursor-pointer" aria-label="Supprimer"><Trash2 class="w-3.5 h-3.5" /></button>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<Modal bind:open={modalOpen} title={editing?.id ? "Modifier la notification" : "Nouvelle notification"} class="max-w-xl">
	{#if editing && overview}
		<form onsubmit={saveRule} class="space-y-5">
			<fieldset>
				<legend class="block text-xs font-medium text-muted mb-1">Quand être prévenu ?</legend>
				<div class="divide-y divide-app-border">
					{#each TRIGGERS as t}
						<label class="flex items-start gap-3 py-2.5 cursor-pointer">
							<input type="radio" name="trigger" checked={editing.trigger === t.id} onchange={() => setTrigger(t.id)} class="mt-0.5 accent-cyan-500" />
							<span>
								<span class="block text-xs font-semibold text-fg">{t.label}</span>
								<span class="block text-[11px] text-muted">{t.hint}</span>
							</span>
						</label>
					{/each}
				</div>
			</fieldset>

			<div>
				<label for="n-name" class="block text-xs font-medium text-muted mb-1">Nom</label>
				<input id="n-name" type="text" bind:value={editing.name} required maxlength="100" class={inputClass} placeholder="Ex : Rappel DS la veille" />
			</div>

			{#if editing.trigger === "deadline"}
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
					<div>
						<label for="n-hours" class="block text-xs font-medium text-muted mb-1">Prévenir combien d'heures avant ?</label>
						<div class="flex gap-2">
							<input id="n-hours" type="number" min="1" max="720" bind:value={editing.params.hours_before} required class={inputClass} />
							<div class="flex gap-1 shrink-0">
								{#each [[2, "2 h"], [24, "1 j"], [72, "3 j"]] as [h, label]}
									<button type="button" onclick={() => (editing!.params.hours_before = h)} class="px-2 rounded-lg bg-app-raised hover:bg-app-raised2 text-[11px] text-muted hover:text-fg cursor-pointer">{label}</button>
								{/each}
							</div>
						</div>
					</div>
					<div>
						<span class="block text-xs font-medium text-muted mb-1">Types concernés (vide = tous)</span>
						<div class="flex flex-wrap gap-1.5">
							{#each CATEGORIES as c}
								<button
									type="button"
									onclick={() => (editing!.params.categories = toggleIn(editing!.params.categories, c.id))}
									class="px-2.5 py-1.5 rounded-lg text-xs cursor-pointer {editing.params.categories.includes(c.id) ? 'bg-cyan-600/15 text-cyan-400 font-semibold' : 'bg-app-raised text-muted'}"
								>{c.label}</button>
							{/each}
						</div>
					</div>
				</div>
				<label class="flex items-center gap-2 text-xs text-muted cursor-pointer">
					<input type="checkbox" bind:checked={editing.params.include_done} class="accent-cyan-500" />
					Me prévenir même si le devoir est déjà marqué comme fait
				</label>
			{:else if editing.trigger === "daily_digest"}
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label for="n-hour" class="block text-xs font-medium text-muted mb-1">Heure d'envoi</label>
						<select id="n-hour" bind:value={editing.params.hour} class={inputClass}>
							{#each Array(24) as _, h}<option value={h}>{String(h).padStart(2, "0")}h00</option>{/each}
						</select>
					</div>
					<div>
						<label for="n-days" class="block text-xs font-medium text-muted mb-1">Échéances des … prochains jours</label>
						<input id="n-days" type="number" min="1" max="14" bind:value={editing.params.days_ahead} required class={inputClass} />
					</div>
				</div>
				<label class="flex items-center gap-2 text-xs text-muted cursor-pointer">
					<input type="checkbox" bind:checked={editing.params.include_done} class="accent-cyan-500" />
					Inclure les devoirs déjà faits
				</label>
			{:else if editing.trigger === "new_week"}
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label for="n-day" class="block text-xs font-medium text-muted mb-1">Jour d'envoi</label>
						<select id="n-day" bind:value={editing.params.day} class={inputClass}>
							{#each DAYS as d, i}<option value={i}>{d}</option>{/each}
						</select>
					</div>
					<div>
						<label for="n-wk-hour" class="block text-xs font-medium text-muted mb-1">Heure d'envoi</label>
						<select id="n-wk-hour" bind:value={editing.params.hour} class={inputClass}>
							{#each Array(24) as _, h}<option value={h}>{String(h).padStart(2, "0")}h00</option>{/each}
						</select>
					</div>
				</div>
				<p class="text-[11px] text-subtle">Nécessite un lien d'emploi du temps dans les Paramètres. L'image est envoyée une seule fois par semaine.</p>
			{/if}

			<div>
				<span class="block text-xs font-medium text-muted mb-1">Envoyer par</span>
				<div class="flex flex-wrap gap-2">
					<button
						type="button"
						disabled={!overview.email_available}
						onclick={() => (editing!.channels = toggleIn(editing!.channels, "email"))}
						class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs disabled:opacity-40 cursor-pointer {editing.channels.includes('email') ? 'bg-cyan-600/15 text-cyan-400 font-semibold' : 'bg-app-raised text-muted'}"
					><Mail class="w-3.5 h-3.5" />Email</button>
					<button
						type="button"
						disabled={!overview.webhook_configured}
						onclick={() => (editing!.channels = toggleIn(editing!.channels, "webhook"))}
						class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs disabled:opacity-40 cursor-pointer {editing.channels.includes('webhook') ? 'bg-cyan-600/15 text-cyan-400 font-semibold' : 'bg-app-raised text-muted'}"
					><Webhook class="w-3.5 h-3.5" />Discord</button>
				</div>
				{#if !overview.email_available || !overview.webhook_configured}
					<p class="text-[11px] text-subtle mt-1.5">
						{#if !overview.webhook_configured}Le webhook Discord se configure dans les Paramètres. {/if}{#if !overview.email_available}L'email nécessite un serveur SMTP configuré par l'administrateur.{/if}
					</p>
				{/if}
			</div>

			{#if error}
				<p class="text-xs text-red-400">{error}</p>
			{/if}

			<div class="flex justify-end gap-2 pt-3 border-t border-app-border">
				<button type="button" onclick={() => (modalOpen = false)} class="px-3.5 py-1.5 rounded-lg bg-app-raised hover:bg-app-raised2 text-xs font-medium text-muted cursor-pointer">Annuler</button>
				<button type="submit" disabled={isSavingRule} class="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold cursor-pointer">
					{isSavingRule ? "Enregistrement..." : "Enregistrer"}
				</button>
			</div>
		</form>
	{/if}
</Modal>
