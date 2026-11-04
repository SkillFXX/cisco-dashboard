<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import { Bell, Mail, Webhook, Plus, Trash2, Pencil, Send, Check, X } from "lucide-svelte";

	type Rule = {
		id?: number;
		name: string;
		enabled: boolean;
		trigger: "new_grade" | "deadline" | "daily_digest";
		params: Record<string, any>;
		channels: string[];
	};

	const TRIGGERS = [
		{ id: "new_grade", label: "Nouvelle note", hint: "Dès qu'une nouvelle note apparaît dans ScoDoc." },
		{ id: "deadline", label: "Avant une échéance", hint: "Un rappel X heures avant un devoir, DM, TP ou DS." },
		{ id: "daily_digest", label: "Récapitulatif quotidien", hint: "Un résumé des échéances à venir, chaque jour à l'heure choisie." }
	] as const;

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

	let webhookInput = $state("");
	let isSavingWebhook = $state(false);

	let editing = $state<Rule | null>(null);
	let isSavingRule = $state(false);

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

	async function saveWebhook(clear = false) {
		isSavingWebhook = true;
		error = "";
		try {
			await api.updateNotificationChannels(clear ? null : webhookInput.trim());
			webhookInput = "";
			await load();
			flash(clear ? "Webhook supprimé." : "Webhook enregistré.");
		} catch (e: any) {
			error = e.message;
		} finally {
			isSavingWebhook = false;
		}
	}

	async function testChannel(channel: "email" | "webhook") {
		error = "";
		try {
			await api.testNotificationChannel(channel);
			flash(channel === "email" ? "Email de test envoyé." : "Message de test envoyé sur le webhook.");
		} catch (e: any) {
			error = e.message;
		}
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

	function startEdit(rule: Rule) {
		editing = JSON.parse(JSON.stringify(rule));
	}

	function setTrigger(trigger: Rule["trigger"]) {
		if (!editing) return;
		editing.trigger = trigger;
		editing.params =
			trigger === "deadline"
				? { hours_before: 24, include_done: false, categories: [] }
				: trigger === "daily_digest"
					? { hour: 18, days_ahead: 3, include_done: false }
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
			editing = null;
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
		return `Chaque jour à ${String(p.hour).padStart(2, "0")}h, échéances des ${p.days_ahead} prochains jours`;
	}

	const inputClass = "w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none";
</script>

<div class="space-y-6">
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
				<Bell class="w-5 h-5 text-cyan-400" />
				<span>Notifications</span>
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">Créez vos alertes : nouvelles notes, rappels de devoirs, récapitulatifs.</p>
		</div>
		{#if overview && !editing}
			<button
				onclick={() => (editing = newRule())}
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
		<!-- Canaux -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
			<Card>
				<div class="flex items-start justify-between gap-3">
					<div class="flex items-center gap-2.5">
						<Mail class="w-4 h-4 text-cyan-400" />
						<h2 class="text-sm font-semibold text-white">Email</h2>
					</div>
					<span class="px-2.5 py-0.5 rounded-full text-[10px] font-medium {overview.email_available ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-400'}">
						{overview.email_available ? "Disponible" : "Indisponible"}
					</span>
				</div>
				<p class="text-xs text-zinc-400 mt-2">
					{#if overview.email_available}
						Les alertes seront envoyées à <span class="text-zinc-200">{overview.email_address}</span>.
					{:else}
						L'administrateur doit d'abord configurer un serveur SMTP.
					{/if}
				</p>
				{#if overview.email_available}
					<button onclick={() => testChannel("email")} class="mt-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-app-border bg-app-surface hover:bg-white/[0.04] text-xs text-zinc-300 cursor-pointer">
						<Send class="w-3.5 h-3.5" />Envoyer un test
					</button>
				{/if}
			</Card>

			<Card>
				<div class="flex items-start justify-between gap-3">
					<div class="flex items-center gap-2.5">
						<Webhook class="w-4 h-4 text-cyan-400" />
						<h2 class="text-sm font-semibold text-white">Webhook Discord</h2>
					</div>
					<span class="px-2.5 py-0.5 rounded-full text-[10px] font-medium {overview.webhook_configured ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-400'}">
						{overview.webhook_configured ? "Configuré" : "Non configuré"}
					</span>
				</div>
				<form
					class="mt-3 flex flex-col sm:flex-row gap-2"
					onsubmit={(e) => {
						e.preventDefault();
						saveWebhook();
					}}
				>
					<input
						type="url"
						bind:value={webhookInput}
						placeholder={overview.webhook_configured ? `Actuel : ${overview.webhook_masked}` : "https://discord.com/api/webhooks/…"}
						aria-label="URL du webhook"
						class={inputClass}
					/>
					<button type="submit" disabled={isSavingWebhook || !webhookInput.trim()} class="px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold cursor-pointer">
						Enregistrer
					</button>
				</form>
				{#if overview.webhook_configured}
					<div class="mt-2 flex gap-2">
						<button onclick={() => testChannel("webhook")} class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-app-border bg-app-surface hover:bg-white/[0.04] text-xs text-zinc-300 cursor-pointer">
							<Send class="w-3.5 h-3.5" />Tester
						</button>
						<button onclick={() => saveWebhook(true)} class="px-3 py-1.5 rounded-lg text-xs text-zinc-400 hover:text-red-400 cursor-pointer">Supprimer</button>
					</div>
				{/if}
				<p class="text-[11px] text-zinc-500 mt-2">Discord : Paramètres du salon → Intégrations → Webhooks → Copier l'URL.</p>
			</Card>
		</div>

		<!-- Formulaire -->
		{#if editing}
			<Card>
				<form onsubmit={saveRule} class="space-y-4">
					<h2 class="text-sm font-semibold text-white">{editing.id ? "Modifier la notification" : "Nouvelle notification"}</h2>

					<div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
						{#each TRIGGERS as t}
							<button
								type="button"
								onclick={() => setTrigger(t.id)}
								class="text-left rounded-lg border p-3 cursor-pointer transition-colors {editing.trigger === t.id ? 'border-cyan-500 bg-cyan-500/10' : 'border-app-border bg-app-surface hover:bg-white/[0.03]'}"
							>
								<div class="text-xs font-semibold text-white">{t.label}</div>
								<div class="text-[11px] text-zinc-400 mt-1">{t.hint}</div>
							</button>
						{/each}
					</div>

					<div>
						<label for="n-name" class="block text-xs font-medium text-zinc-400 mb-1">Nom</label>
						<input id="n-name" type="text" bind:value={editing.name} required maxlength="100" class={inputClass} placeholder="Ex : Rappel DS la veille" />
					</div>

					{#if editing.trigger === "deadline"}
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label for="n-hours" class="block text-xs font-medium text-zinc-400 mb-1">Prévenir combien d'heures avant ?</label>
								<div class="flex gap-2">
									<input id="n-hours" type="number" min="1" max="720" bind:value={editing.params.hours_before} required class={inputClass} />
									<div class="flex gap-1 shrink-0">
										{#each [[2, "2 h"], [24, "1 j"], [72, "3 j"]] as [h, label]}
											<button type="button" onclick={() => (editing!.params.hours_before = h)} class="px-2 rounded-lg border border-app-border bg-app-surface text-[11px] text-zinc-300 hover:text-white cursor-pointer">{label}</button>
										{/each}
									</div>
								</div>
							</div>
							<div>
								<span class="block text-xs font-medium text-zinc-400 mb-1">Types concernés (vide = tous)</span>
								<div class="flex flex-wrap gap-1.5">
									{#each CATEGORIES as c}
										<button
											type="button"
											onclick={() => (editing!.params.categories = toggleIn(editing!.params.categories, c.id))}
											class="px-2.5 py-1.5 rounded-lg text-xs cursor-pointer {editing.params.categories.includes(c.id) ? 'bg-white/[0.12] text-white font-semibold' : 'border border-app-border bg-app-surface text-zinc-400'}"
										>{c.label}</button>
									{/each}
								</div>
							</div>
						</div>
						<label class="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer">
							<input type="checkbox" bind:checked={editing.params.include_done} class="accent-cyan-500" />
							Me prévenir même si le devoir est déjà marqué comme fait
						</label>
					{:else if editing.trigger === "daily_digest"}
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label for="n-hour" class="block text-xs font-medium text-zinc-400 mb-1">Heure d'envoi</label>
								<select id="n-hour" bind:value={editing.params.hour} class={inputClass}>
									{#each Array(24) as _, h}<option value={h}>{String(h).padStart(2, "0")}h00</option>{/each}
								</select>
							</div>
							<div>
								<label for="n-days" class="block text-xs font-medium text-zinc-400 mb-1">Échéances des … prochains jours</label>
								<input id="n-days" type="number" min="1" max="14" bind:value={editing.params.days_ahead} required class={inputClass} />
							</div>
						</div>
						<label class="flex items-center gap-2 text-xs text-zinc-300 cursor-pointer">
							<input type="checkbox" bind:checked={editing.params.include_done} class="accent-cyan-500" />
							Inclure les devoirs déjà faits
						</label>
					{/if}

					<div>
						<span class="block text-xs font-medium text-zinc-400 mb-1">Envoyer par</span>
						<div class="flex flex-wrap gap-2">
							<button
								type="button"
								disabled={!overview.email_available}
								onclick={() => (editing!.channels = toggleIn(editing!.channels, "email"))}
								class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs disabled:opacity-40 cursor-pointer {editing.channels.includes('email') ? 'bg-white/[0.12] text-white font-semibold' : 'border border-app-border bg-app-surface text-zinc-400'}"
							><Mail class="w-3.5 h-3.5" />Email</button>
							<button
								type="button"
								disabled={!overview.webhook_configured}
								onclick={() => (editing!.channels = toggleIn(editing!.channels, "webhook"))}
								class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs disabled:opacity-40 cursor-pointer {editing.channels.includes('webhook') ? 'bg-white/[0.12] text-white font-semibold' : 'border border-app-border bg-app-surface text-zinc-400'}"
							><Webhook class="w-3.5 h-3.5" />Discord / webhook</button>
						</div>
					</div>

					<div class="flex justify-end gap-2 pt-2 border-t border-app-border">
						<button type="button" onclick={() => (editing = null)} class="px-3.5 py-1.5 rounded-lg border border-app-border bg-app-surface hover:bg-white/[0.04] text-xs font-medium text-zinc-300 cursor-pointer">Annuler</button>
						<button type="submit" disabled={isSavingRule} class="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold cursor-pointer">
							{isSavingRule ? "Enregistrement..." : "Enregistrer"}
						</button>
					</div>
				</form>
			</Card>
		{/if}

		<!-- Liste -->
		{#if overview.rules.length === 0 && !editing}
			<div class="py-10 text-center border border-dashed border-app-border rounded-xl bg-app-card/40 text-zinc-500 text-xs">
				Aucune notification pour l'instant. Créez-en une pour être prévenu automatiquement.
			</div>
		{:else}
			<div class="border border-app-border rounded-xl bg-app-card overflow-hidden divide-y divide-white/5">
				{#each overview.rules as rule (rule.id)}
					<div class="flex items-center gap-3 p-3.5">
						<button
							onclick={() => toggleRule(rule)}
							role="switch"
							aria-checked={rule.enabled}
							aria-label="Activer {rule.name}"
							class="relative w-9 h-5 rounded-full shrink-0 transition-colors cursor-pointer {rule.enabled ? 'bg-cyan-600' : 'bg-zinc-700'}"
						>
							<span class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform {rule.enabled ? 'translate-x-4' : ''}"></span>
						</button>
						<div class="min-w-0 flex-1">
							<div class="text-xs font-bold text-white truncate">{rule.name}</div>
							<div class="text-xs text-zinc-400 truncate">{describe(rule)}</div>
						</div>
						<div class="hidden sm:flex items-center gap-1.5 text-zinc-500">
							{#if rule.channels.includes("email")}<Mail class="w-3.5 h-3.5" />{/if}
							{#if rule.channels.includes("webhook")}<Webhook class="w-3.5 h-3.5" />{/if}
						</div>
						<button onclick={() => startEdit(rule)} class="p-1.5 text-zinc-400 hover:text-white cursor-pointer" aria-label="Modifier"><Pencil class="w-3.5 h-3.5" /></button>
						<button onclick={() => removeRule(rule)} class="p-1.5 text-zinc-400 hover:text-red-400 cursor-pointer" aria-label="Supprimer"><Trash2 class="w-3.5 h-3.5" /></button>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>
