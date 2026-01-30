%module eggwrapper
%feature("autodoc", "0");
%include "std_string.i"
%include "exception.i"
%include "typemaps.i"
%exception {
    try {
        $action
    }
    catch (const egglib::EggArgumentValueError& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggFormatError& e) {
        SWIG_exception(SWIG_IOError, e.what());
    }
    catch (const egglib::EggInvalidAlleleError& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggInvalidCharacterError& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggMemoryError& e) {
        SWIG_exception(SWIG_MemoryError, e.what());
    }
    catch (const egglib::EggOpenFileError& e) {
        SWIG_exception(SWIG_IOError, e.what());
    }
    catch (const egglib::EggRuntimeError& e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    }
    catch (const egglib::EggIndexError& e) {
        SWIG_exception(SWIG_IndexError, e.what());
    }
    catch (const egglib::EggUnalignedError& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggNonHierarchicalStructure& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggPloidyError& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggInvalidChromosomeIdxError& e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    }
    catch (const egglib::EggInvalidPositionIdxError& e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    }
    catch (const egglib::EggAlphabetError<int>& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggAlphabetError<char>& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggAlphabetError<const char *>& e) {
        SWIG_exception(SWIG_ValueError, e.what());
    }
    catch (const egglib::EggInvalidLineIdxError& e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    }
    catch (const egglib::EggException& e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    }
    catch (const std::exception& e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    }
}

%{
// this is to suppress warnings from eggwrapper.cpp
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wmaybe-uninitialized"
%}

%{
#include "egglib.hpp"
#include "AlleleStatus.hpp"
#include "Alphabet.hpp"
#include "Coalesce.hpp"
#include "DataHolder.hpp"
#include "Rd.hpp"
#include "Diversity1.hpp"
#include "Diversity2.hpp"
#include "Fs.hpp"
#include "ParalogPi.hpp"
#include "EHH.hpp"
#include "Fasta.hpp"
#include "Export.hpp"
#include "GeneticCode.hpp"
#include "GFF3.hpp"
#include "Haplotypes.hpp"
#include "LD.hpp"
#include "Lineage.hpp"
#include "Params.hpp"
#include "SiteDiversity.hpp"
#include "SiteHolder.hpp"
#include "FreqHolder.hpp"
#include "Structure.hpp"
#include "Tree.hpp"
#include "VCF.hpp"
#include "ComputeV.hpp"
#include "VcfWindow.hpp"
#include "BED.hpp"

// this is to fix an include fail of swig
#include <cstddef>
%}

// add this to add in import at the beginning of the python code
//%pythonbegin %{
//%}

%rename(VcfFilter) egglib::vcf::Filter;
%apply int& INOUT {int& code};

namespace egglib {
    // pre-declarations
    class VcfParser;
    class VcfIndex;
    class Coalesce;
    class Params;
    class SiteHolder;
    class StructureCluster;
    class StructurePopulation;
    class StructureIndiv;
    class BedParser;
    class Alphabet;
    // classes
    class VectorInt {
        public:
            VectorInt();
            virtual ~VectorInt();
            VectorInt(const VectorInt& src);
            void set_num_values(unsigned int n);
            unsigned int get_num_values() const;
            void set_item(unsigned int i, int value);
            int get_item(unsigned int i) const;
            void clear();
    };
    %nodefaultctor AbstractBaseAlphabet;
    class AbstractBaseAlphabet {
        public:
            void lock();
            bool is_locked() const;
            void set_name(const char * name);
            const char * get_name() const;
            virtual unsigned int num_exploitable() const;
            virtual unsigned int num_missing() const;
            const char * get_type() const;
            void set_type(const char *);
            virtual bool case_insensitive() const;
    };
    template <class TYPE> class AbstractTemplateAlphabet : public AbstractBaseAlphabet {
        public:
            AbstractTemplateAlphabet();
            virtual const TYPE get_value(int code) = 0;
            virtual int get_code(const TYPE value) = 0;
    };
    template <class TYPE> class FiniteAlphabet : public AbstractTemplateAlphabet<TYPE> {
        public:
            FiniteAlphabet();
            virtual const TYPE get_value(int code);
            virtual int get_code(const TYPE value);
            virtual void add_exploitable(const TYPE value);
            virtual void add_missing(const TYPE value);
            virtual unsigned int num_exploitable() const;
            virtual unsigned int num_missing() const;
    };
    %template(IntBaseAlphabet) AbstractTemplateAlphabet<int>;
    %template(CharBaseAlphabet) AbstractTemplateAlphabet<char>;
    %template(CStringBaseAlphabet) AbstractTemplateAlphabet<char *>;
    %template(IntAlphabet) FiniteAlphabet<int>;
    %template(CharAlphabet) FiniteAlphabet<char>;
    %template(CStringAlphabet) FiniteAlphabet<char *>;
    class CaseInsensitiveCharAlphabet : public FiniteAlphabet<char> {
        public:
            CaseInsensitiveCharAlphabet();
            virtual void add_exploitable(const char value);
            virtual void add_missing(const char value);
            virtual bool case_insensitive() const;
    };
    class DNAAlphabet : public CaseInsensitiveCharAlphabet {
        public:
            DNAAlphabet();
    };
    class StringAlphabet: public FiniteAlphabet<char *> {
        public:
            StringAlphabet();
            virtual int get_code(const char * value);
            virtual void add_exploitable(char * const value);
            virtual void add_missing(char * const value);
            unsigned int longest_length() const;
    };
    class CodonAlphabet : public StringAlphabet {
        public:
            CodonAlphabet();
            virtual int get_code(const char * value);
            int get_code_from_bases(int, int, int);
            virtual unsigned int num_exploitable();
            virtual unsigned int num_missing();
            virtual void add_exploitable(const char * value);
            virtual void add_missing(const char * value);
    };
    class CaseInsensitiveStringAlphabet: public StringAlphabet {
        public:
            CaseInsensitiveStringAlphabet();
            virtual bool case_insensitive() const;
    };
    class CustomStringAlphabet : public StringAlphabet {
        public:
            CustomStringAlphabet();
    };
    class RangeAlphabet : public AbstractTemplateAlphabet<int> {
        public:
            RangeAlphabet();
            virtual int get_code(const int);
            virtual const int get_value(int code);
            int first_exploitable() const;
            int end_exploitable() const;
            int first_missing() const;
            int end_missing() const;
            void set_exploitable(int, int);
            void set_missing(int, int);
            int min_value() const;
            int max_value() const;
            virtual unsigned int num_exploitable() const;
            virtual unsigned int num_missing() const;
    };
    class DataHolder {
        public:
            DataHolder(bool is_matrix = false);
            DataHolder(const DataHolder& src);
            virtual ~DataHolder();
            bool valid_phyml_names() const;
            void set_is_matrix(bool flag);
            bool get_is_matrix() const;
            void reserve(unsigned int ns, unsigned int ln,
                         unsigned int ng, unsigned int ls);
            unsigned int get_nsam() const;
            void set_nsam(unsigned int nsam);
            unsigned int get_nsit_all() const;
            unsigned int get_nsit_sample(unsigned int sam) const;
            void set_nsit_all(unsigned int nsit);
            void set_nsit_sample(unsigned int sam, unsigned int nsit);
            void insert_sites_all(unsigned int pos, unsigned int num);
            void insert_sites_sample(unsigned int sam, unsigned int pos, unsigned int num);
            unsigned int get_nlabels(unsigned int) const;
            void set_nlabels(unsigned int, unsigned int);
            int get_sample(unsigned int sam, unsigned int sit) const;
            void set_sample(unsigned int sam, unsigned int sit, int value);
            const char * get_label(unsigned int sam, unsigned int lvl) const;
            void set_label(unsigned int sam, unsigned int lvl, const char * label);
            void add_label(unsigned int sam, const char * label);
            const char * get_name(unsigned int sam) const;
            void set_name(unsigned int sam, const char * name);
            void name_appendch(unsigned int sam, char ch);
            void name_append(unsigned int sam, const char * ch);
            void del_sample(unsigned int sam);
            void del_sites_all(unsigned int start, unsigned int stop);
            void del_sites_sample(unsigned int sam, unsigned int start, unsigned int stop);
            void reset(bool is_matrix);
            void clear(bool is_matrix);
            void change_case(bool lower, int index_i, int start_i, int stop_i, AbstractBaseAlphabet& alph);
            unsigned int find(unsigned int sam, VectorInt& values, unsigned int start=0, unsigned int stop=MAX) const;
            bool is_equal() const;
            void strip_clear();
            void strip_add(int);
            void strip(unsigned int index, bool left, bool right);
    };
    class IntersperseAlign {
        public:
            IntersperseAlign();
            ~IntersperseAlign();
            void load(DataHolder& data);
            void set_length(unsigned int length);
            void set_position(unsigned int index, double position);
            void set_round_position(unsigned int index, unsigned int position);
            void get_positions(const Coalesce& coalesce);
            void set_num_alleles(unsigned int num);
            void set_allele(unsigned int index, int allele);
            void intersperse(bool round_positions = true);
    };
    class StructureHolder {
        public:
            StructureHolder();
            ~StructureHolder();
            void reset();
            void check_ploidy(unsigned int value=UNKNOWN);
            unsigned int get_ploidy() const;
            bool outgroup_haploid() const;
            void get_structure(DataHolder& data, unsigned int lvl_clust,
                    unsigned int lvl_pop, unsigned int lvl_indiv,
                    unsigned int ploidy, bool skip_outgroup, const char * outgroup_label);
            void mk_dummy_structure(unsigned int, unsigned int);
            void dummy_add_pop(unsigned int);
            void process_ingroup(unsigned int idx, const char * lbl_clust,
                const char * lbl_pop, const char * lbl_indiv);
            void process_outgroup(unsigned int idx, const char * lbl_indiv);
            StructureCluster * add_cluster(const char * label);
            StructurePopulation * add_population(const char * label, StructureCluster * cluster);
            StructureIndiv * add_individual_ingroup(const char * label, StructurePopulation * population);
            StructureIndiv * add_individual_outgroup(const char * label);
            void StructureHolder::add_sample_ingroup(unsigned int sam_idx, StructureIndiv * indiv);
            void StructureHolder::add_sample_outgroup(unsigned int sam_idx, StructureIndiv * indiv);
            unsigned int num_clust() const;
            unsigned int num_pop() const;
            unsigned int num_indiv_ingroup() const;
            unsigned int num_indiv_outgroup() const;
            const StructureCluster& get_cluster(unsigned int idx) const;
            const StructurePopulation& get_population(unsigned int idx) const;
            const StructureIndiv& get_indiv_ingroup(unsigned int idx) const;
            const StructureIndiv& get_indiv_outgroup(unsigned int idx) const;
            unsigned int get_ni() const;
            unsigned int get_no() const;
            unsigned int get_req() const;
            void copy(const StructureHolder& source);
            const char * subset(const StructureHolder& source, char * popstring, char * cluststring, bool outgroup);
            void shuffle_init(int mode);
            void shuffle();
            void shuffle_restore();
            unsigned int init_i();
            unsigned int init_o();
            unsigned int iter_i();
            unsigned int iter_o();
    };
    class StructureCluster {
        public:
            StructureCluster(const char * label);
            ~StructureCluster();
            void reset(const char * label);
            StructurePopulation * add_pop(const char * label);
            unsigned int num_pop() const;
            const StructurePopulation& get_population(unsigned int idx) const;
            const char * get_label() const;
    };
    class StructurePopulation {
        public:
            StructurePopulation(const char * label);
            ~StructurePopulation();
            void reset(const char * label);
            StructureIndiv * add_indiv(const char * label);
            unsigned int num_indiv() const;
            const StructureIndiv& get_indiv(unsigned int idx) const;
            const char * get_label() const;
    };
    class StructureIndiv {
        public:
            StructureIndiv(const char * label);
            ~StructureIndiv();
            void reset(const char * label);
            unsigned int num_samples() const;
            void add_sample(unsigned int index);
            unsigned int get_sample(unsigned int idx) const;
            const char * get_label() const;
    };
    class FreqSet {
        public:
            FreqSet();
            ~FreqSet();
            void setup();
            void set_nall(unsigned int);
            void add_genotypes(unsigned int num);
            void incr_allele(unsigned int all_idx, unsigned int num);
            void incr_genotype(unsigned int gen_idx, unsigned int num);
            void tell_het(unsigned int i, unsigned int a);
            unsigned int num_alleles() const;
            unsigned int num_alleles_eff() const;
            unsigned int num_genotypes() const;
            unsigned int num_genotypes_eff() const;
            unsigned int nseff() const;
            unsigned int nieff() const;
            unsigned int frq_all(unsigned int) const;
            unsigned int frq_gen(unsigned int) const;
            unsigned int frq_het(unsigned int) const;
            unsigned int tot_het() const;
    };
    class FreqHolder {
        public:
            FreqHolder();
            ~FreqHolder();
            void setup_structure(const StructureHolder& structure);
            void setup_raw(unsigned int nc, unsigned int np, unsigned int ploidy);
            void setup_pop(unsigned int i, unsigned int clu_idx, unsigned int rel_idx, unsigned int ns);
            void set_ngeno(unsigned int ng);
            void process_site(const SiteHolder& site);
            void process_vcf(const VcfParser& vcf);
            const FreqSet& frq_ingroup() const;
            const FreqSet& frq_outgroup() const;
            unsigned int num_clusters() const;
            unsigned int num_populations() const;
            const FreqSet& frq_cluster(unsigned int) const;
            const FreqSet& frq_population(unsigned int) const;
            unsigned int num_alleles() const;
            int allele(unsigned int) const;
            unsigned int get_allele_index(int) const;
            unsigned int ploidy() const;
            unsigned int num_genotypes() const;
            bool genotype_het(unsigned int) const;
            const int * genotype(unsigned int) const;
            int genotype_item(unsigned int, unsigned int) const;
            void set_genotype_item(unsigned int i, unsigned int j, int a);
            unsigned int find_allele(int);
            unsigned int cluster_index(unsigned int) const;
    };
    class AlleleStatus {
        public:
            AlleleStatus();
            ~AlleleStatus();
            void reset();
            void process(const FreqHolder& freqs);
            void total();
            unsigned int nsites() const;
            unsigned int nsites_o() const;
            unsigned int Sp() const;
            unsigned int Sp_T1() const;
            unsigned int Spd() const;
            unsigned int Spd_T1() const;
            unsigned int ShP() const;
            unsigned int ShP_T1() const;
            unsigned int ShA() const;
            unsigned int ShA_T1() const;
            unsigned int FxA() const;
            unsigned int FxA_T1() const;
            unsigned int FxD() const;
            unsigned int FxD_T1() const;
    };
    class GeneticCode {
        public:
            GeneticCode(unsigned int index=1);
            unsigned int get_code() const;
            void set_code(unsigned int index);
            bool start(int codon) const;
            bool is_stop_unsmart(int codon) const;
            double NSsites(int codon, bool ignorestop = true) const;
            double Ssites(int codon, bool ignorestop = true) const;
            int translate(int);
            const char * name() const;
            double NSsites(const SiteHolder& site, unsigned int& num_samples, bool ignorestop = true) const;
            double Ssites(const SiteHolder& site, unsigned int& num_samples, bool ignorestop = true) const;
            static inline unsigned int ndiff(int codon1, int codon2);
            static inline bool diff1(int codon1, int codon2);
            static inline bool diff2(int codon1, int codon2);
            static inline bool diff3(unsigned int codon1, unsigned int codon2);
            static unsigned int num_codes();
    };
    class SiteDiversity {
        public:
            SiteDiversity();
            void f3focus(unsigned int);
            void f4flag(bool);
            virtual ~SiteDiversity();
            void toggle_off();
            void toggle_fstats_diplo();
            void toggle_fstats_haplo();
            void toggle_fstats_hier();
            void toggle_hstats();
            void set_maf(double);
            unsigned long process(const FreqHolder&);
            unsigned int average();
            double ns() const;
            double nso() const;
            unsigned int k() const;
            unsigned int npop_eff1() const;
            unsigned int npop_eff2() const;
            unsigned int npop_eff3() const;
            unsigned int nclu_eff() const;
            double Aglob() const;
            double Aing() const;
            double Aout() const;
            int global_allele(unsigned int) const;
            double S() const;
            double Sd() const;
            double R() const;
            double He() const;
            double Ho() const;
            double He_pop(unsigned int pop) const;
            double pairdiff_inter(unsigned int pop1, unsigned int pop2) const;
            bool orientable() const;
            double derived(unsigned int) const;
            double a() const;
            double b() const;
            double c() const;
            double a0() const;
            double b1() const;
            double b2() const;
            double c0() const;
            double n() const;
            double d() const;
            double f2() const;
            double f3() const;
            double f4() const;
            double Dp() const;
            double Hst() const;
            double Gst() const;
            double Gste() const;
            double D() const;
            double thetaIAM() const;
            double thetaSMM() const;
            double maf() const;
            double maf_pop(unsigned int) const;
            unsigned int num_pop() const;
            void reset();
            unsigned int nsites1() const;
            unsigned int nsites2() const;
            unsigned int nsites3() const;
            unsigned int nsites4() const;
            unsigned int nsites5() const;
            unsigned int nsites6() const;
            unsigned int nsites7() const;
            unsigned int nsites8() const;
            unsigned int nsites9() const;
            unsigned int nsites10() const;
            unsigned int nsites11() const;
            unsigned int nsites12() const;
    };
    class SiteHolder {
        public:
            SiteHolder();
            virtual ~SiteHolder();
            void reset();
            double get_position() const;
            void set_position(double);
            const char * get_chrom() const;
            void set_chrom(const char *);
            void add(unsigned int num);
            void set_sample(unsigned int sam, int allele);
            unsigned int get_ns() const;
            int get_sample(unsigned int sam) const;
            void del_sample(unsigned int);
            unsigned int get_missing() const;
            unsigned int process_align(const DataHolder& data,
                        unsigned int idx, StructureHolder* struc=NULL);
            unsigned int process_vcf(VcfParser& data,
                             unsigned int start, unsigned int stop);
    };
    class Genotypes {
        public:
            Genotypes();
            ~Genotypes();
            void process(const SiteHolder&, StructureHolder&, bool);
            unsigned int ploidy() const;
            const SiteHolder& site() const;
            bool heter(unsigned int) const;
            const int * const genot(unsigned int) const;
            unsigned int num_genotypes() const;
    };
    class Diversity1 {
        public:
            Diversity1();
            ~Diversity1();
            void load(const FreqHolder& freqs, const SiteDiversity& div, double position);
            unsigned int compute();
            void reset_stats();
            void toggle_off();
            void toggle_ori_site();
            void toggle_ori_div();
            void toggle_basic();
            void toggle_site_lists();
            void set_option_multiple(bool);
            void set_option_ns_set(unsigned int);
            unsigned int lt() const;
            unsigned int ls() const;
            unsigned int lso() const; 
            unsigned int S() const;
            unsigned int Ss() const;
            unsigned int So() const;
            unsigned int Sso() const;
            unsigned int nsingld() const;
            unsigned int site(unsigned int) const;
            unsigned int site_o(unsigned int) const;
            unsigned int singl(unsigned int) const;
            unsigned int singl_o(unsigned int) const;
            unsigned int nall(unsigned int) const;
            unsigned int frq(unsigned int, unsigned int) const;
            unsigned int frqp(unsigned int, unsigned int, unsigned int) const;
            unsigned int eta() const;
            unsigned int etao() const;
            double D() const;
            double Deta() const; 
            double Dstar() const;
            double Fstar() const;
            double thetaW() const;
            double Pi() const; 
            double Dxy() const;
            double Da() const;
            double nseff() const;
            unsigned int nsmax() const;
            double nseffo() const;
            unsigned int nsmaxo() const;
            double thetaH() const;
            double thetaPi() const;
            double thetaL() const;
            double Hns() const;
            double Hsd() const;
            double E() const;
            double Dfl() const;
            double F() const;
            double pM() const;
            unsigned int nM() const;
    };
    class Diversity2 {
        public:
            Diversity2();
            ~Diversity2();
            void reset();
            void reset_stats();
            void set_structure(StructureHolder&);
            void load(const SiteHolder&, const SiteDiversity&, const FreqHolder&);
            unsigned int num_sites() const;
            unsigned int num_orientable() const;
            unsigned int num_clear() const;
            unsigned int num_samples() const;
            void toggle_off();
            void toggle_singletons();
            void toggle_partitions();
            void set_option_multiple(bool);
            unsigned int compute();
            double k() const;
            double ko() const;
            double R2() const;
            double R3() const;
            double R4() const;
            double Ch() const;
            double R2E() const;
            double R3E() const;
            double R4E() const;
            double ChE() const;
            double B() const;
            double Q() const;
    };
    class Haplotypes {
        public:
            Haplotypes();
            ~Haplotypes();
            void setup(const StructureHolder&);
            void set_structure(const StructureHolder&);
            void reset_stats();
            void load(const Genotypes&);
            void prepare_impute(unsigned int);
            void resolve(const Genotypes&);
            void cp_haplotypes();
            void impute();
            void cp_dist();
            unsigned int cp_stats();
            unsigned int n_ing() const;
            unsigned int n_otg() const;
            unsigned int n_sam() const;
            unsigned int nt_hapl() const;
            unsigned int hapl(unsigned int, unsigned int) const;
            unsigned int map_sample(unsigned int) const;
            unsigned int n_sites() const;
            unsigned int ne_ing() const;
            unsigned int ne_otg() const;
            unsigned int n_missing(unsigned int) const;
            unsigned int n_mis() const;
            unsigned int mis_idx(unsigned int) const;
            unsigned int ni_hapl() const;
            unsigned int ng_hapl() const;
            unsigned int freq_i(unsigned int) const;
            unsigned int freq_o(unsigned int) const;
            unsigned int n_potential(unsigned int) const;
            unsigned int potential(unsigned int, unsigned int) const;
            unsigned int dist(unsigned int, unsigned int) const;
            double Fst() const;
            double Kst() const;
            double Snn() const;
            unsigned int n_pop() const;
            unsigned int ne_pop() const;
            void get_site(SiteHolder&);
            bool invalid() const;
    };
    class PairwiseLD {
        public:
            PairwiseLD();
            ~PairwiseLD();
            bool process(const SiteHolder& site1, const SiteHolder& site2, const FreqHolder&, const FreqHolder&, StructureHolder&, unsigned min_n = 2, double max_maj = 1.0);
            unsigned int num_alleles1() const;
            unsigned int num_alleles2() const;
            unsigned int index1(unsigned int allele) const;
            unsigned int index2(unsigned int allele) const;
            unsigned int freq1(unsigned int allele) const;
            unsigned int freq2(unsigned int allele) const;
            unsigned int freq(unsigned int allele1, unsigned int allele2) const;
            unsigned int nsam() const;
            void compute(unsigned int allele1, unsigned int allele2);
            double D() const;
            double Dp() const;
            double r() const;
            double rsq() const;
            void reset();
    };
    class MatrixLD {
        public:
            MatrixLD();
            ~MatrixLD();
            void reset();
            void set_structure(StructureHolder&);
            void load(const Genotypes& genosite, double position);
            void computeLD(unsigned min_n = 2, double max_maj = 1.0);
            unsigned int num_tot() const;
            unsigned int num_pairs() const;
            unsigned int num_alleles() const;
            const PairwiseLD& pairLD(unsigned int index) const;
            unsigned int index1(unsigned int allele) const;
            unsigned int index2(unsigned int allele) const;
            unsigned int distance(unsigned int index) const;
            enum MultiAllelic {
                ignore,
                use_main,
                use_all
            };
            void computeStats(MultiAllelic multiallelic = ignore, unsigned int min_freq = 0);
            unsigned int num_allele_pairs() const;
            unsigned int num_allele_pairs_adj() const;
            double ZnS() const;
            double ZnS_star1() const;
            double ZnS_star2() const;
            double Za() const;
            double ZZ() const;
            void computeRmin(bool oriented=false);
            unsigned int Rmin() const;
            unsigned int Rmin_num_sites() const;
            unsigned int Rmin_left(unsigned int i) const;
            unsigned int Rmin_right(unsigned int i) const;
            void toggle_off();
            void toggle_Rmin();
            void toggle_stats();
            unsigned int MatrixLD::process(unsigned min_n, double max_maj, MultiAllelic multiallelic, unsigned int min_freq, bool oriented);
    };
    class ParalogPi {
        public:
            ParalogPi();
            ~ParalogPi();
            void reset(const StructureHolder& str_prl, const StructureHolder& str_idv, double max_missing);
            void load(const SiteHolder&);
            unsigned int num_sites_tot() const;
            unsigned int num_sites_paralog(unsigned int) const;
            unsigned int num_sites_pair(unsigned int, unsigned int) const;
            unsigned int num_samples() const;
            unsigned int num_paralogs() const;
            double Piw(unsigned int) const;
            double Pib(unsigned int, unsigned int) const;
    };
    class Rd {
        public:
            Rd();
            virtual ~Rd();
            void load(const SiteHolder&);
            void configure(const StructureHolder&);
            double compute();
            unsigned int num_loci() const;
            unsigned int ploidy() const;
            unsigned int num_indiv() const;
            void reset();
            void reset_stats();
    };
    class Migration {
        public:
            Migration(unsigned int n, double M);
            ~Migration();
            unsigned int n() const;
            void set_all(double M);
            void set_all_R(double M);
            void set_row(unsigned int i, double M);
            void set_row_R(unsigned int i, double M);
            void set_pair(unsigned int i, unsigned int j, double m);
            void set_pair_R(unsigned int i, unsigned int j, double m);
            double get_row(unsigned int i) const;
            double get_pair(unsigned int i, unsigned int j) const;
            void restore();
    };
    class Event {
        public:
            enum Type { none, change_N, change_M, change_Mp, change_G,
                        change_s, change_R,  bottleneck, admixture,
                        delayed };
        public:
            Event(Type, double);
            void copy(const Event& src);
            Type event_type() const;
            double date() const;
            double get_param() const;
            unsigned int get_index() const;
            unsigned int get_dest() const;
            unsigned int get_number1() const;
            unsigned int get_number2() const;
            void perform(Params * param, Coalesce * coal);
            void insert(Event * event);
            void disconnect();
            Event * next();
            Event * prev();
            void move(double date);
            void set_index(unsigned int i);
            void set_param(double p);
            void set_dest(unsigned int d);
            void set_number1(unsigned int n);
            void set_number2(unsigned int n);
            const char * get_label() const;
            void set_label(const char *);
    };
    class Params {
        public:
            enum MutationModel { KAM, IAM, SMM, TPM };
            Params();
            Params(unsigned int npop, double migr=0.0);
            ~Params();
            std::string summary() const;
            unsigned int k() const;
            unsigned int get_K() const;
            void set_K(unsigned int value);
            unsigned long get_max_iter() const;
            void set_max_iter(unsigned long);
            bool get_random_start_allele() const;
            void set_random_start_allele(bool value);
            void set_R(double value);
            void R_R(double value);
            double get_R() const;
            void set_theta(double value);
            double get_theta() const;
            void set_fixed(unsigned int value);
            unsigned int get_fixed() const;
            void set_mutmodel(MutationModel value);
            MutationModel get_mutmodel() const;
            void set_TPMproba(double value);
            double get_TPMproba() const;
            void set_TPMparam(double value);
            double get_TPMparam() const;
            void set_n1(unsigned int pop, unsigned int value);
            unsigned int get_n1(unsigned int pop) const;
            void set_n2(unsigned int pop, unsigned int value);
            unsigned int get_n2(unsigned int pop) const;
            void set_N(unsigned int pop, double value);
            void N_R(unsigned int pop, double value, double t);
            double get_N(unsigned int pop) const;
            void set_G(unsigned int pop, double value);
            void G_R(unsigned int pop, double value, double t);
            double get_G(unsigned int pop) const;
            void set_s(unsigned int pop, double value);
            void s_R(unsigned int pop, double value, double t);
            double get_s(unsigned int pop) const;
            unsigned int get_L() const;
            void set_L(unsigned int value);
            void autoSitePos();
            void set_sitePos(unsigned int site, double value);
            double get_sitePos(unsigned int site) const;
            void set_siteW(unsigned int site, double value);
            double get_siteW(unsigned int site) const;
            double totalSiteW() const;
            Migration & M();
            void set_transW_matrix(bool flag);
            bool get_transW_matrix() const;
            void set_transW_pair(unsigned int i, unsigned int j, double value);
            double get_transW_pair(unsigned int i, unsigned int j) const;
            double get_transW_row(unsigned int i) const;
            void addChange(Event * e);
            void clearChanges();
            unsigned int numChanges() const;
            Event * firstChange();
            double nextChangeDate() const;
            void nextChangeDo(Coalesce * coal);
            unsigned int nDSChanges() const;
            double lastChange(unsigned int pop) const;
            void restore();
            void validate() const;
            unsigned int get_nsam();
    };
    class Node {
        public:
            Node();
            Node(const Node& src);
            virtual ~Node();
            void set_internal(double t, unsigned int son1, unsigned int son2);
            void set_terminal(double t, unsigned int label);
            bool is_terminal() const;
            unsigned int label() const;
            unsigned int son1() const;
            unsigned int son2() const;
            double date() const;
            double get_L() const;
            void set_L(double value);
            unsigned int nmut() const;
            unsigned int mutationSite(unsigned int mut) const;
            double mutationPos(unsigned int mut) const;
            void addMutation(unsigned int site, double pos);
            void reset();
            void clear_mutations();
    };
    class Tree {
        public:
            Tree(unsigned int numberOfLeaves, double start, double stop);
            Tree(const Tree& tree);
            virtual ~Tree();
            void recomb(double point, Tree * new_tree);
            unsigned int coal(unsigned int nodeIndex1, unsigned int nodeIndex2, double time);
            unsigned int mutate(unsigned int site, DataHolder& data, const Params * params);
            double start() const;
            double stop() const;
            double cov() const;
            double L() const;
            Node * root() const;
            unsigned int nnodes() const;
            Node * const node(unsigned int i) const;
            unsigned int addNode(double t, unsigned int label);
            void reset(unsigned int numberOfLeaves, double start, double stop);
            void clear_mutations();
    };
    class Coalesce {
        public:
            Coalesce();
            ~Coalesce();
            void simul(Params *params, bool mutate=true);
            void mutate();
            void coalescence(unsigned int pop, unsigned int i, unsigned int j);
            void migrate(unsigned int source, unsigned int i, unsigned int dest);
            void admixt(unsigned int source, unsigned int dest, double proba);
            void bottleneck(unsigned int pop, double duration);
            unsigned int number_of_trees() const;
            void delayedSample(double date, unsigned int pop, unsigned int n1, unsigned int n2);
            Tree const * const tree(unsigned int i) const;
            DataHolder const * const data() const;
            double tree_start(unsigned int i) const;
            double tree_stop(unsigned int i) const;
            double site_position(unsigned int mut) const;
    };
    class EHH {
        public:
            EHH();
            virtual ~EHH();
            void set_core(const SiteHolder * site, StructureHolder * struct_indiv,
                          double EHH_thr, double EHHc_thr,
                          double EHHS_thr, double EHHG_thr, unsigned int min_freq, unsigned int min_sam, bool crop);
            void load_distant(const SiteHolder * site);
            unsigned int K_core() const;
            unsigned int K_cur() const;
            unsigned int num_avail_tot() const;
            unsigned int num_avail_core(unsigned int) const;
            unsigned int num_avail_cur(unsigned int) const;
            double EHHS() const;
            double EHHG() const;
            double EHHi(unsigned int haplotype) const;
            double EHHc(unsigned int haplotype) const;
            double rEHH(unsigned int haplotype) const;
            double iES() const;
            double iEG() const;
            double iHH(unsigned int haplotype) const;
            double iHHc(unsigned int haplotype) const;
            double iHS(unsigned int haplotype) const;
            unsigned int num_EHH_done() const;
            unsigned int num_EHHc_done() const;
            bool flag_EHHS_done() const;
            bool flag_EHHG_done() const;
            double dEHH(unsigned int haplotype) const;
            double dEHHc(unsigned int haplotype) const;
            double dEHH_max() const;
            double dEHH_mean() const;
            double dEHHS() const;
            double dEHHG() const;
    };
    class BaseFormatter {
        public:
            BaseFormatter();
            virtual ~BaseFormatter();
            bool open_file(const char * fname);
            void to_str();
            std::string get_str();
            void to_cout();
            void write(const char * bit, bool eol);
            void flush();
            void close();
    };
    class Export : public BaseFormatter {
        public:
            Export();
            ~Export();
            void newick(const Tree& tree, bool blen, bool eol);
            void ms_num_positions(unsigned int n);
            void ms_position(unsigned int site, double position);
            void ms_auto_positions(unsigned int n);
            void ms(const DataHolder& data, bool spacer);
    };
    class FastaFormatter : public BaseFormatter {
        public:
            FastaFormatter();
            virtual ~FastaFormatter();
            void defaults();
            void set_first(unsigned int first = 0);
            void set_last(unsigned int last = MAX);
            void set_labels(bool labels = true);
            void set_linelength(unsigned int linelength = 50);
            void write(const DataHolder& src, AbstractBaseAlphabet& alph);
            std::string write_string(const DataHolder& src, AbstractBaseAlphabet& alph);
    };
    class FastaParser {
      public:
        FastaParser();
        ~FastaParser();
        void reserve(unsigned int ln, unsigned int ls, unsigned int ng, unsigned int lf);
        void open_file(const char * fname, FiniteAlphabet<char>&, unsigned int offset=0);
        void set_string(const char * str, FiniteAlphabet<char>&);
        void read_sequence(bool groups, DataHolder * dest = NULL, char label_marker='@', char label_separator=' ');
        void read_all(bool groups, DataHolder& dest, char label_marker='@', char label_separator=' ');
        void close();
        bool good() const;
        const char * name() const;
        unsigned int ls() const;
        char ch(unsigned int index) const;
        unsigned int nlabels() const;
        const char * label(unsigned int index) const;
        void clear();
    };
    class Feature {
      public:
        friend class GFF3;
        enum PHASE {
            zero,
            one,
            two,
            no_phase
        };
        enum STRAND {
            plus,
            minus,
            no_strand
        };
        Feature();
        virtual ~Feature();
        void reset();
        void clear();
        const char * get_seqid() const;
        void set_seqid(const char * str);
        const char * get_source() const;
        void set_source(const char * str);
        const char * get_type() const;
        void set_type(const char * str);
        unsigned int get_num_fragments() const;
        void set_num_fragments(unsigned int num);
        unsigned int get_start(unsigned int i) const;
        void set_start(unsigned int i, unsigned int val);
        unsigned int get_end(unsigned int i) const;
        void set_end(unsigned int i, unsigned int val);
        double get_score() const;
        void set_score(double d);
        STRAND get_strand() const;
        void set_strand(STRAND s);
        PHASE get_phase() const;
        void set_phase(PHASE p);
        const char * get_ID() const;
        void set_ID(const char * str);
        const char * get_Name() const;
        void set_Name(const char * str);
        unsigned int get_num_Alias() const;
        void set_num_Alias(unsigned int num);
        const char * get_Alias(unsigned int i) const;
        void set_Alias(unsigned int i, const char * s);
        unsigned int get_num_Parent() const;
        void set_num_Parent(unsigned int num);
        const char * get_Parent(unsigned int i) const;
        void set_Parent(unsigned int i, const char * s);
        const char * get_Target() const;
        void set_Target(const char * str);
        const char * get_Gap() const;
        void set_Gap(const char * str);
        const char * get_Derives_from() const;
        void set_Derives_from(const char * str);
        unsigned int get_num_Note() const;
        void set_num_Note(unsigned int num);
        const char * get_Note(unsigned int i) const;
        void set_Note(unsigned int i, const char * s);
        unsigned int get_num_Dbxref() const;
        void set_num_Dbxref(unsigned int num);
        const char * get_Dbxref(unsigned int i) const;
        void set_Dbxref(unsigned int i, const char * s);
        unsigned int get_num_Ontology_term() const;
        void set_num_Ontology_term(unsigned int num);
        const char * get_Ontology_term(unsigned int i) const;
        void set_Ontology_term(unsigned int i, const char * s);
        bool get_Is_circular() const;
        void set_Is_circular(bool b);
        unsigned int get_num_attributes() const;
        void set_num_attributes(unsigned int num);
        unsigned int get_num_items_attribute(unsigned int i) const;
        void set_num_items_attribute(unsigned int i, unsigned int num);
        const char * get_attribute_key(unsigned int i) const;
        void set_attribute_key(unsigned int i, const char * str);
        const char * get_attribute_value(unsigned int attr, unsigned int item) const;
        void set_attribute_value(unsigned int attr, unsigned int item, const char * str);
        unsigned int get_num_parents() const;
        void set_num_parents(unsigned int num);
        Feature * get_parent(unsigned int i) const;
        void set_parent(unsigned int i, Feature * feat);
        unsigned int get_num_parts() const;
        void set_num_parts(unsigned int num);
        Feature * get_part(unsigned int i) const;
        void set_part(unsigned int i, Feature * feat);
    };
    class GFF3 {
      public:
        GFF3();
        virtual ~GFF3();
        void liberal(bool flag);
        void parse(const char* fname);
        void parse(std::istream& stream);
        void parse_string(std::string& string);
        void reset();
        void clear();
        unsigned int num_metadata() const;
        const char * metadata_key(unsigned int i) const;
        const char * metadata_value(unsigned int i) const;
        unsigned int num_genes() const;
        Feature& gene(unsigned int i);
        unsigned int num_features() const;
        Feature& feature(unsigned int i);
        const DataHolder& sequences() const;
    };
    namespace vcf {
        enum AltType { Default, Referred, Breakend };
        const unsigned int NUM_ALTERNATE;
        const unsigned int NUM_GENOTYPES;
        const unsigned int NUM_POSSIBLE_ALLELES;
        class Filter {
          public:
            Filter();
            Filter(const char * id, const char * descr);
            Filter(const Filter& src);
            virtual ~Filter();
            void update(const char * id, const char * descr);
            const char * get_ID() const;
            void set_ID(const char * id);
            const char * get_description() const;
            void set_description(const char * descr);
            void clear();
            void set_extra(const char * key, const char * value);
            const char * get_extra_key(unsigned int idx) const;
            const char * get_extra_value(unsigned int idx) const;
            unsigned int get_num_extra() const;
        };
        class Info : public Filter {
          public:
            enum Type { Integer, Float, Flag, Character, String };
            Info();
            Info(const char * id, unsigned int num, Info::Type t, const char * descr);
            Info(const Info& src);
            void update(const char * id, unsigned int num, Info::Type t, const char * descr);
            unsigned int get_number() const;
            void set_number(unsigned int num);
            virtual Info::Type get_type() const;
            virtual  void set_type(Info::Type t);
        };
        class Format : public Info {
          public:
            Format();
            Format(const char * id, unsigned int num, Info::Type t, const char * descr);
            Format(const Format& src);
            Format(const Info& src);
            void update(const char * id, unsigned int num, Info::Type t, const char * descr);
            virtual Info::Type get_type() const;
            virtual void set_type(Info::Type t);
        };
        class Meta {
          public:
            Meta();
            Meta(const char * k, const char * v);
            Meta(Meta& src);
            ~Meta();
            void update(const char * k, const char * v);
            void set_key(const char * k);
            void set_value(const char * v);
            const char * get_key() const;
            const char * get_value() const;
            void clear();
        };
        class Alt : public Filter {
          public:
            Alt();
            Alt(const char * id, const char * descr);
            Alt(Alt& src);
            Alt(Filter& src);
            ~Alt() {}
        };
        class FlagInfo {
          public:
            friend class egglib::VcfParser;
            FlagInfo();
            FlagInfo(const FlagInfo& src);
            virtual ~FlagInfo();
            void set_ID(const char * id);
            const char * get_ID() const;
        };
        template <class T> class TypeInfo : public FlagInfo {
          public:
            friend class egglib::VcfParser;
            TypeInfo();
            TypeInfo(const TypeInfo<T>& src);
            virtual ~TypeInfo();
            unsigned int num_items() const;
            const T& item(unsigned int i) const;
            void reset();
            unsigned int get_expected_number();
            void set_expected_number(unsigned int);
        };
        %template(TypeInfoString) TypeInfo<char *>;
        %template(TypeInfoInt) TypeInfo<int>;
        %template(TypeInfoChar) TypeInfo<char>;
        %template(TypeInfoDouble) TypeInfo<double>;
        class StringInfo : public TypeInfo<char *> {
          public:
            friend class egglib::VcfParser;
            StringInfo();
            StringInfo(const StringInfo& src);
            virtual ~StringInfo();
            const char * item(unsigned int item);
            void change(unsigned int item, unsigned int position, char value);
        };
        class SampleInfo {
          public:
            friend class egglib::VcfParser;
            SampleInfo();
            SampleInfo(const SampleInfo& src);
            ~SampleInfo();
            void reset();
            void clear();
            unsigned int num_IntegerEntries() const;
            unsigned int num_IntegerItems(unsigned int i) const;
            int IntegerItem(unsigned int i, unsigned int j) const;
            unsigned int num_FloatEntries() const;
            unsigned int num_FloatItems(unsigned int i) const;
            double FloatItem(unsigned int i, unsigned int j) const;
            unsigned int num_CharacterEntries() const;
            unsigned int num_CharacterItems(unsigned int i) const;
            char CharacterItem(unsigned int i, unsigned int j) const;
            unsigned int num_StringEntries() const;
            unsigned int num_StringItems(unsigned int i) const;
            const char * StringItem(unsigned int i, unsigned int j) const;
        };
    }
    class VcfParser {
      public:
        VcfParser();
        virtual ~VcfParser();
        void open_file(const char* fname);
        void set_stream(std::istream& stream);
        void read_header(const char *);
        void set_threshold_PL(unsigned int);
        void set_threshold_GL(unsigned int);
        unsigned int get_threshold_PL() const;
        unsigned int get_threshold_GL() const;
        void allow_X(bool);
        void allow_gap(bool);
        void read();
        void readline(const char *);
        unsigned long get_currline() const;
        bool good() const;
        bool has_data() const;
        void reset();
        void reset_variant();
        void clear();
        const char * file_format() const;
        unsigned int num_filter() const;
        const vcf::Filter * get_filter(unsigned int i) const;
        unsigned int num_info() const;
        const vcf::Info * get_info(unsigned int i) const;
        unsigned int num_format() const;
        const vcf::Format * get_format(unsigned int i) const;
        unsigned int num_meta() const;
        const vcf::Meta * get_meta(unsigned int i) const;
        unsigned int num_alt() const;
        const vcf::Alt * get_alt(unsigned int i) const;
        void add_filter(const char * id, const char * descr);
        void add_alt(const char * id, const char * descr);
        void add_info(const char * id, unsigned int num, vcf::Info::Type type, const char * descr);
        void add_format(const char * id, unsigned int num, vcf::Info::Type type, const char * descr);
        void add_meta(const char * key, const char * val);
        unsigned int num_samples() const;
        const char * get_sample(unsigned int i) const;
        vcf::Filter * find_filter(const char * id);
        vcf::Format * find_format(const char * id);
        vcf::Info * find_info(const char * id);
        vcf::Meta * find_meta(const char * key);
        vcf::Alt * find_alt(const char * id);
        const char * chromosome() const;
        unsigned long position() const;
        unsigned int num_ID() const;
        const char * ID(unsigned int i) const;
        unsigned int len_reference() const;
        const char * reference() const;
        unsigned int num_alternate() const;
        vcf::AltType alternate_type(unsigned int i) const;
        const char * alternate(unsigned int i) const;
        double quality() const;
        unsigned int num_failed_tests() const;
        const char * failed_test(unsigned int i) const;
        unsigned int num_FlagInfo() const;
        const vcf::FlagInfo FlagInfo(unsigned int) const;
        unsigned int num_IntegerInfo() const;
        const vcf::TypeInfo<int>& IntegerInfo(unsigned int) const;
        unsigned int num_FloatInfo() const;
        const vcf::TypeInfo<double>& FloatInfo(unsigned int) const;
        unsigned int num_CharacterInfo() const;
        const vcf::TypeInfo<char>& CharacterInfo(unsigned int) const;
        unsigned int num_StringInfo() const;
        const vcf::StringInfo& StringInfo(unsigned int) const;
        unsigned int num_fields() const;
        const vcf::Format& field(unsigned int i) const;
        unsigned int field_index(const char * ID) const;
        unsigned int field_rank(unsigned int i) const;
        unsigned int field_rank(const char * ID) const;
        const vcf::SampleInfo& sample_info(unsigned int i) const;
        bool has_AN() const;
        unsigned int AN() const;
        bool has_AA() const;
        const char * AA_string() const;
        unsigned int AA_index() const;
        bool has_AC() const;
        unsigned int num_AC() const;
        unsigned int AC(unsigned int i) const;
        bool has_AF() const;
        unsigned int num_AF() const;
        double AF(unsigned int i) const;
        bool has_GT() const;
        unsigned int ploidy() const;
        unsigned int num_genotypes() const;
        bool GT_phased(unsigned int i) const;
        bool GT_phased() const;
        unsigned int GT(unsigned int sample, unsigned int allele) const;
        bool has_PL() const;
        bool has_GL() const;
        unsigned int PL(unsigned int sample, unsigned int genotype) const;
        double GL(unsigned int sample, unsigned int genotype) const;
        void unread();
        VcfIndex& get_index();
        void rewind();
        unsigned int type_alleles() const;
        void set_alleles(StringAlphabet&);
    };
    class VcfIndex {
        public:
            void go_to(const char *, unsigned long);
            unsigned long num() const;
            bool has_data() const;
            void load_data(VcfParser&, const char * fname);
    };
    %nodefaultctor WSite;
    class WSite {
      public:
        SiteHolder& site();
        StringAlphabet * alphabet();
        unsigned int get_pos() const;
        WSite * next();
        WSite * prev();
    };
    %nodefaultctor VcfWindowBase;
    class VcfWindowBase {
        public:
            VcfWindowBase();
            virtual ~VcfWindowBase();
            void setup_base(VcfParser&, unsigned int max_missing, unsigned int mask);
            const char * chromosome() const;
            unsigned int num_samples() const;
            unsigned int num_sites() const;
            unsigned long win_start() const;
            unsigned long win_stop() const;
            const WSite * first_site() const;
            const WSite * last_site() const;
            bool good() const;
            const WSite * get_site(unsigned int) const;
            virtual void next_window() = 0;
    };
    %nodefaultctor VcfWindowSliderBase;
    class VcfWindowSliderBase : public VcfWindowBase {
        public:
            VcfWindowSliderBase();
            virtual ~VcfWindowSliderBase();
            virtual void setup(VcfParser& parser, unsigned int wsize, unsigned int wstep,
                unsigned long start_pos, unsigned long stop_pos,
                unsigned int max_missing, unsigned int mask);
            virtual void next_window() = 0;
    };
    class VcfWindowSlider : public VcfWindowSliderBase {
        public:
            VcfWindowSlider();
            virtual void setup(VcfParser& parser, unsigned int wsize, unsigned int wstep,
                unsigned long start_pos, unsigned long stop_pos,
                unsigned int max_missing, unsigned int mask);
            virtual ~VcfWindowSlider();
            virtual void next_window();
    };
    class VcfWindowSliderPerSite : public VcfWindowSliderBase {
        public:
            VcfWindowSliderPerSite();
            virtual ~VcfWindowSliderPerSite();
            virtual void next_window();
    };
    class VcfWindowBED : public VcfWindowBase {
        public:
            VcfWindowBED();
            virtual ~VcfWindowBED();
            void setup(VcfParser& parser, BedParser&, unsigned int max_missing, unsigned int mask);
            virtual void next_window();
    };
    class BedParser {
        public:
            BedParser();
            ~BedParser();
            void get_bed_file(const char * filename);
            unsigned int n_bed_data();
            const char * get_chrom(unsigned int);
            unsigned long get_start(unsigned int);
            unsigned long get_end(unsigned int);
            void append(const char *, unsigned long, unsigned long);
    };
    class ComputeV {
        public:
            ComputeV();
            ~ComputeV();
            void reset();
            bool compute(const FreqHolder&, AbstractTemplateAlphabet<int>&);
            double average_V() const;
            double average_Ar() const;
            double average_M() const;
            double average_Rst() const;
            double curr_V() const;
            double curr_Ar() const;
            double curr_M() const;
            double curr_Rst() const;
            unsigned int num_sites() const;
            unsigned int num_sites_m() const;
            unsigned int num_sites_rst() const;
            void set_maf(double);
    };
    class Triconfigurations {
        public:
            Triconfigurations();
            ~Triconfigurations();
            void reset();
            void set_min(unsigned int);
            void process(const FreqHolder &);
            unsigned int num() const;
            unsigned int cnt(unsigned int) const;
    };

    // global variables
    const int MISSINGDATA;
    const int MAX_ALLELE_RANGE;
    const double UNDEF;
    const unsigned int UNKNOWN;
    const unsigned int MAX;
    const char MAXCHAR;
    const unsigned int OUTGROUP;
    const unsigned int MISSING;
    const unsigned long BEFORE;
    const unsigned long FIRST;
    const unsigned long LAST;
    DNAAlphabet& get_static_DNAAlphabet();
    CodonAlphabet& get_static_CodonAlphabet();
    const int DEBUG_FLAG;

    // global functions
    void read_fasta_file(const char * fname, bool labels, DataHolder& dest, FiniteAlphabet<char>&);
    void read_fasta_string(const std::string str, bool labels, DataHolder& dest, FiniteAlphabet<char>&);
    double Fs(unsigned int n, unsigned int K, double pi);
    void make_vcf_index(egglib::VcfParser& VCF, const char * output);
}
