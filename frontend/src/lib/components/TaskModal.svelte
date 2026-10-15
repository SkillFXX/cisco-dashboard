<script lang="ts">
	import Modal from "./Modal.svelte";
	import Button from "./Button.svelte";
	import { api } from "$lib/api";

	let {
		open = $bindable(false),
		onTaskCreated
	}: {
		open: boolean;
		onTaskCreated?: () => void;
	} = $props();

	let title = $state("");
	let subject = $state("R101 - Initiation aux Réseaux");
	let event_type = $state("ds");
	let due_date = $state("");
	let description = $state("");
	let isSubmitting = $state(false);
	let error = $state("");

	// Set default date to 3 days ahead at 10:00
	$effect(() => {
		if (open && !due_date) {
			const d = new Date();
			d.setDate(d.getDate() + 3);
			d.setHours(10, 0, 0, 0);
			due_date = d.toISOString().slice(0, 16);
		}
	});

	const subjectsList = [
		"R101 - Initiation aux Réseaux Informatiques",
		"R102 - Principes des Télécoms & Signal",
		"R103 - Bases de l'Électronique Numérique",
		"R107 - Administration Système sous Linux",
		"R108 - Algorithmique et Programmation Réseau",
		"SAÉ 1.1 - Déploiement Réseau PME",
		"Mathématiques du Signal",
		"Anglais Technique & Réseaux",
		"Autre Matière"
	];

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!title.trim()) {
			error = "Veuillez entrer un titre.";
			return;
		}
		if (!due_date) {
			error = "Veuillez choisir une date d'échéance.";
			return;
		}

		isSubmitting = true;
		error = "";

		try {
			await api.createTask({
				title,
				subject,
				event_type,
				due_date: new Date(due_date).toISOString(),
				description: description.trim() || undefined,
				status: "todo"
			});
			open = false;
			title = "";
			description = "";
			if (onTaskCreated) onTaskCreated();
		} catch (err: any) {
			error = err.message || "Erreur lors de la création de la tâche.";
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Modal bind:open title="Ajouter un Événement ou un DS" description="Planifiez vos contrôles, rendus de TP ou rappels personnels.">
	<form onsubmit={handleSubmit} class="space-y-4">
		{#if error}
			<div class="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
				{error}
			</div>
		{/if}

		<div>
			<label for="task-type" class="block text-xs font-medium text-zinc-400 mb-1.5">Type d'évaluation</label>
			<div class="grid grid-cols-4 gap-2">
				{#each [
					{ id: 'ds', label: 'Devoir Surveillé (DS)' },
					{ id: 'dm', label: 'Devoir Maison (DM)' },
					{ id: 'tp', label: 'TP Noté' },
					{ id: 'todo', label: 'Rappel / To-Do' }
				] as item}
					<button
						type="button"
						onclick={() => (event_type = item.id)}
						class="rounded-lg border px-2 py-2 text-xs font-medium text-center transition-all cursor-pointer {event_type === item.id ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400 font-semibold' : 'border-zinc-800 bg-zinc-950/60 text-zinc-400 hover:border-zinc-700'}"
					>
						{item.label}
					</button>
				{/each}
			</div>
		</div>

		<div>
			<label for="task-title" class="block text-xs font-medium text-zinc-400 mb-1">Titre de l'épreuve / tâche *</label>
			<input
				id="task-title"
				type="text"
				bind:value={title}
				placeholder="Ex: DS 2 - Routage OSPF & Adressage VLSM"
				required
				class="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none"
			/>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<div>
				<label for="task-subject" class="block text-xs font-medium text-zinc-400 mb-1">Matière associée</label>
				<select
					id="task-subject"
					bind:value={subject}
					class="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none"
				>
					{#each subjectsList as sub}
						<option value={sub}>{sub}</option>
					{/each}
				</select>
			</div>

			<div>
				<label for="task-date" class="block text-xs font-medium text-zinc-400 mb-1">Date et heure limite *</label>
				<input
					id="task-date"
					type="datetime-local"
					bind:value={due_date}
					required
					class="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none"
				/>
			</div>
		</div>

		<div>
			<label for="task-desc" class="block text-xs font-medium text-zinc-400 mb-1">Consignes ou notes (facultatif)</label>
			<textarea
				id="task-desc"
				bind:value={description}
				rows="3"
				placeholder="Chapitres à réviser, calculatrice autorisée, salle de l'examen..."
				class="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none resize-none"
			></textarea>
		</div>

		<div class="flex justify-end gap-2 pt-2 border-t border-zinc-800">
			<Button variant="outline" onclick={() => (open = false)} disabled={isSubmitting}>
				Annuler
			</Button>
			<Button variant="cisco" type="submit" disabled={isSubmitting}>
				{isSubmitting ? "Enregistrement..." : "Enregistrer le DS"}
			</Button>
		</div>
	</form>
</Modal>

