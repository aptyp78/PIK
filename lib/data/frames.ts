/**
 * Static definitions of PIK frames and their fields.
 *
 * These definitions come from the PIK v5.0 methodology.  Each frame has
 * a name, a slug and a list of field names.  Later iterations of the
 * project will load these values from the database and map extracted
 * blocks to these fields.
 */

export interface FrameTemplate {
  slug: string;
  name: string;
  fields: string[];
}

export const frames: FrameTemplate[] = [
  {
    slug: 'platform-experience',
    name: 'Platform Experience',
    fields: [
      'Stakeholder',
      'Services',
      'Key Expectations',
      'Motivation',
      'Key Resources',
      'Alternatives',
      'Satisfaction Drivers Success Factors',
      'Attract',
      'Touchpoints',
      'CRM',
      'Key Insights',
      'Basic',
      'Delight'
    ]
  },
  {
    slug: 'ecosystem-forces-scan',
    name: 'Ecosystem Forces Scan',
    fields: [
      'Environment',
      'Market',
      'Macroeconomic',
      'Value Chain',
      'Emerging Needs'
    ]
  },
  {
    slug: 'platform-business-model',
    name: 'Platform Business Model',
    fields: [
      'Mission',
      'Core Services',
      'Core Value Proposition',
      'Core Network Effects',
      'Consumers',
      'Producers',
      'Value Capture',
      'Cost Structure',
      'Key People Skills',
      'Key Data',
      'Key Infrastructure',
      'Supporters',
      'Investors',
      'Suppliers',
      'USP',
      'TAM',
      'SAM',
      'SOM'
    ]
  },
  {
    slug: 'nfx-reinforcement-engines',
    name: 'NFX Reinforcement Engines',
    fields: [
      'Demand Side',
      'Supply Side',
      'Core Value',
      'Brand Loyalty',
      'Tech Infrastructure',
      'Economy of Scale',
      'Experience Personal Social',
      'Ecosystem Sustainability',
      'Data Intelligence'
    ]
  },
  {
    slug: 'platform-value-network',
    name: 'Platform Value Network',
    fields: [
      'Consumers',
      'Producers',
      'Partners',
      'Owners',
      'Value Propositions',
      'Transactions'
    ]
  }
];
