import { useState } from 'react'

import { Checkbox } from '@/components/ui/checkbox'
import { Field, FieldContent, FieldDescription, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { InputGroup, InputGroupAddon, InputGroupInput, InputGroupText } from '@/components/ui/input-group'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'

import { KitDemo, KitSection } from './KitSection'

export function FormsSection() {
  const [notify, setNotify] = useState(true)

  return (
    <KitSection
      id="forms"
      title="Forms"
      description="Label above control, helper or error below. Use form.tsx (react-hook-form) for real forms; Field for layout."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <KitDemo title="Text inputs" className="block">
          <FieldGroup className="gap-5">
            <Field>
              <FieldLabel htmlFor="kit-name">Project name</FieldLabel>
              <Input id="kit-name" placeholder="Acme dashboard" />
              <FieldDescription>Visible to everyone in the workspace.</FieldDescription>
            </Field>
            <Field data-invalid="true">
              <FieldLabel htmlFor="kit-email">Email</FieldLabel>
              <Input id="kit-email" type="email" defaultValue="not-an-email" aria-invalid="true" />
              <FieldError>Enter a valid email address</FieldError>
            </Field>
            <Field>
              <FieldLabel htmlFor="kit-search">Search with addons</FieldLabel>
              <InputGroup>
                <InputGroupAddon>
                  <i className="ph ph-magnifying-glass" aria-hidden="true" />
                </InputGroupAddon>
                <InputGroupInput id="kit-search" placeholder="Search…" />
                <InputGroupAddon align="inline-end">
                  <InputGroupText>⌘K</InputGroupText>
                </InputGroupAddon>
              </InputGroup>
            </Field>
            <Field>
              <FieldLabel htmlFor="kit-about">About</FieldLabel>
              <Textarea id="kit-about" placeholder="A short description…" />
            </Field>
          </FieldGroup>
        </KitDemo>
        <KitDemo title="Choices" className="block">
          <FieldGroup className="gap-5">
            <Field>
              <FieldLabel htmlFor="kit-role">Role</FieldLabel>
              <Select defaultValue="editor">
                <SelectTrigger id="kit-role" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="viewer">Viewer</SelectItem>
                  <SelectItem value="editor">Editor</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field orientation="horizontal">
              <Checkbox id="kit-terms" defaultChecked />
              <FieldLabel htmlFor="kit-terms" className="font-normal">
                Send me product updates
              </FieldLabel>
            </Field>
            <Field orientation="horizontal" className="justify-between rounded-lg border p-4">
              <FieldContent>
                <FieldLabel htmlFor="kit-notify">Email notifications</FieldLabel>
                <FieldDescription>Get a daily summary of activity.</FieldDescription>
              </FieldContent>
              <Switch id="kit-notify" checked={notify} onCheckedChange={setNotify} />
            </Field>
            <RadioGroup defaultValue="monthly" className="grid-cols-2">
              {['monthly', 'yearly'].map((plan) => (
                <Label
                  key={plan}
                  htmlFor={`kit-${plan}`}
                  className="flex items-center gap-3 rounded-lg border p-3 font-normal capitalize has-data-[state=checked]:border-primary has-data-[state=checked]:bg-primary/5"
                >
                  <RadioGroupItem id={`kit-${plan}`} value={plan} />
                  {plan}
                </Label>
              ))}
            </RadioGroup>
          </FieldGroup>
        </KitDemo>
      </div>
      <KitDemo title="Tabs" className="block">
        <div className="grid gap-6 lg:grid-cols-2">
          <Tabs defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
            <TabsContent value="overview" className="text-sm text-muted-foreground">
              Segmented tabs — for switching views inside a card.
            </TabsContent>
            <TabsContent value="activity" className="text-sm text-muted-foreground">
              Activity
            </TabsContent>
            <TabsContent value="settings" className="text-sm text-muted-foreground">
              Settings
            </TabsContent>
          </Tabs>
          <Tabs defaultValue="general">
            <TabsList variant="line">
              <TabsTrigger value="general">General</TabsTrigger>
              <TabsTrigger value="members">Members</TabsTrigger>
              <TabsTrigger value="billing">Billing</TabsTrigger>
            </TabsList>
            <TabsContent value="general" className="text-sm text-muted-foreground">
              Line tabs — for page-level sections.
            </TabsContent>
            <TabsContent value="members" className="text-sm text-muted-foreground">
              Members
            </TabsContent>
            <TabsContent value="billing" className="text-sm text-muted-foreground">
              Billing
            </TabsContent>
          </Tabs>
        </div>
      </KitDemo>
    </KitSection>
  )
}
