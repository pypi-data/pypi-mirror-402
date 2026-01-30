/*
    Copyright 2008-2021 Stéphane De Mita, Mathieu Siol

    This file is part of the EggLib library.

    EggLib is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    EggLib is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with EggLib.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef EGGLIB_FASTA_HPP
#define EGGLIB_FASTA_HPP

#include <istream>
#include <fstream>
#include <sstream>
#include <string>
#include <iostream>
#include <limits>
#include "egglib.hpp"
#include "DataHolder.hpp"
#include "Export.hpp"

namespace egglib {

    template <class TYPE> class FiniteAlphabet;
    class AbstractBaseAlphabet;

   /** \brief Sequence-by-sequence Fasta parser
    *
    * \ingroup parsers
    *
    * Read fasta-formatted sequence data from a file specified by name
    * or from an open stream. See the description of the format below.
    *
    *    - Each sequence is preceded by a header limited to a single
    *      line and starting by a ">" character.
    *
    *    - The header length is not limited and all characters are
    *      allowed but white spaces and special characters are
    *      discouraged. The header is terminated by a newline character.
    *
    *    - Group labels are specified a special markup system placed at
    *      the end of the header line.
    *
    *    - Group labels are ignored unless specifically specified in a
    *      parser's options.
    *
    *    - The sequence itself continues on following lines until the
    *      next ">" character or the end of the file.
    *
    *    - White spaces, tab and carriage returns are allowed at any
    *      position. They are ignored unless for terminating the header
    *      line. There is no limitation in length and different
    *      sequences can have different lengths.
    *
    *    - Characters case is preserved and imported. Note that, when
    *      *groups* is true and that sequences are placed in a
    *      DataHolder instance, their position in the original fasta
    *      file is lost. Exporting to fasta will automatically place
    *      them at the end of the file.
    *
    * Header: <egglib-cpp/Fasta.hpp>
    *
    */
    class FastaParser {

      public:

       /** \brief Constructor
        *
        * The constructor does not generate an object ready for use.
        * Call to open or set methods is needed before starting to
        * parse data.
        *
        */
        FastaParser();

       /** \brief Destructor
        *
        */
        ~FastaParser();

       /** \brief Reserve memory to speed up data loading
        *
        * This method does not change the size of the data set
        * contained in the instance, but reserves memory in order to
        * speed up subsequent loading of data. The passed values are not
        * required to be accurate. In case the instance has allocated
        * more memory than what is requested, nothing is done (this
        * applies to all parameters independently). It is always valid
        * to use 0 for any values (in that case, no memory is pre
        * allocated for the corresponding array, and memory will be
        * allocated when needed). Note that one character is always
        * pre-allocated for all names.
        *
        * \param ln expected length of name.
        * \param ls expected length of sequence.
        * \param ng expected number of groups.
        * \param lf expected length of file name.
        *
        */
        void reserve(unsigned int ln, unsigned int ls, unsigned int ng, unsigned int lf);

       /** \brief Open a file for reading
        *
        * This method attempts to open the specified file and to read a
        * single character. If the file cannot be open, an
        * EggOpenFileError exception is thrown; if the read character is
        * not '>', an EggFormatError exception is thrown; if the file is
        * empty, no exception is thrown.
        *
        * In case the instance was already processing a stream, it will
        * be dismissed. The stream created by this method will be closed
        * if another stream is created or set (call to open_file() or set_stream()
        * methods), if the close() method is called or upon object
        * destruction.
        *
        * \param fname name of the fasta-formatted file to open.
        * \param alph alphabet to use for checking characters.
        * \param offset start position in file.
        *
        */
        void open_file(const char * fname, FiniteAlphabet<char>& alph, unsigned int offset=0);

       /** \brief Pass an open stream for reading
        *
        * This method sets the passed stream (which is supposed to have
        * been opened for reading) and attempts to read a single
        * character. If the stream is not open or if data cannot be read
        * from it, an EggArgumentValueError (and not EggOpenFileError)
        * exception is thrown; if the read character is not '>', an
        * EggFormatError exception is thrown; if no data is found, no
        * exception is thrown.
        *
        * In case the instance was already processing a stream, it will
        * be dismissed. The stream passed by this method not be closed
        * by the class even when calling close().
        *
        * \param stream open stream to read fasta-formatted sequences from.
        * \param alph alphabet to use for checking characters.
        *
        */
        void set_stream(std::istream& stream, FiniteAlphabet<char>& alph);

       /** \brief Pass a string for reading
        *
        * This method opens a reading stream initialized on the passed
        * string and attempts to read a single character. If data cannot
        * be read, an EggArgumentValueError (and not EggOpenFileError)
        * exception is thrown; if the read character is not '>', an
        * EggFormatError exception is thrown; if no data is found, no
        * exception is thrown.
        *
        * In case the instance was already processing a stream, it will
        * be dismissed.
        *
        * \param str a string to be read.
        * \param alph alphabet to use for checking characters.
        *
        */
        void set_string(const char * str, FiniteAlphabet<char>& alph);

       /** \brief Read a single sequence
        *
        * If the argument *dest* is NULL (default):
        *
        * Read a sequence from the stream and load it in the object
        * memory. Read data can be accessed using name(), ch() and
        * group() methods (plus outgroup() and group_o() for an outgroup
        * sequence). Note that memory allocated for storing data is
        * retained after subsequent calls to read() (but not data
        * themselves). This means that subsequent sequences will be read
        * faster. It also means that, after reading a long sequence,
        * memory will be used until destruction of the object or call to
        * clear() method. Note that read data will be lost as soon as
        * the current stream is dismissed (using the close() method), or
        * a new stream is opened or set, or clear() is called, or read()
        * is called again with a NULL *dest* argument, but not if read()
        * is called with a non-NULL *dest* argument.
        *
        * If the argument *dest* is **not** NULL:
        *
        * Read a sequence from the stream and load it into the passed
        * DataHolder instance. This will result in the addition of one
        * sequence to the DataHolder. Warning:
        * *dest* must absolutely be a non-matrix.
        *
        * In either case:
        *
        * If no data can be read (no open stream, stream closed or
        * reached end of file), an EggRuntimeError exception will be
        * thrown.
        *
        * \param groups if false, any group labels found in sequence
        *  headers will be ignored.
        *
        * \param dest if not NULL, destination where to place read data
        * (otherwise, data are stored within the current instance).
        *
        * \param label_marker character indicating the start of the labels.
        *
        * \param label_separator character used to separate labels.
        *
        */
        void read_sequence(bool groups, DataHolder * dest=NULL, char label_marker='@', char label_separator=',');

       /** \brief Read a multiple sequences into a DataHolder
        *
        * This method calls read() repetitively passing the DataHolder
        * reference which is filled incrementally, until the end of the
        * fasta stream is reached. If the DataHolder instance already
        * contains sequences, new sequences are appended at the end.
        * Warning: *dest* must absolutely be a non-matrix.
        *
        * \param groups if false, any group labels found in sequence
        * headers will be ignored.
        *
        * \param dest destination where to place read data.
        *
        * \param label_marker character indicating the start of the labels.
        *
        * \param label_separator character used to separate labels.
        *
        */
        void read_all(bool groups, DataHolder& dest, char label_marker='@', char label_separator=',');

       /** \brief Close the open file
        *
        * This method closes the file that was opened using the
        * open_file() method. If the file was open using the open_file() method of
        * the same instance, it is actually closed. If the file was
        * passed as a stream using set_stream(), it is forgotten but not
        * closed. If no stream is present, this method does nothing.
        *
        */
        void close();

       /** \brief Check if the instance is good for reading
        *
        * Return true if an open stream is available and if the last
        * reading operation (or by default opening) found that the next
        * character is a '>'.
        *
        */
        bool good() const;

       /** \brief Get the last read name
        *
        * Return a c-string containing the name of the last sequence
        * read by the read() method. By default, an empty string is
        * returned.
        *
        */
        const char * name() const;

       /** \brief Get the length of the last read sequence
        *
        * Return the length of the last sequence read by the read()
        * method. By default, the value is 0.
        *
        */
        unsigned int ls() const;

       /** \brief Get a character of the last read sequence
        *
        * Get the value of a specified index of the last sequence read
        * by the read() method. The index must be valid.
        *
        */
        char ch(unsigned int index) const;

       /** \brief Get the number of group labels specified for the last read sequence
        *
        * Return the number group labels specified for the last sequence
        * read by the read() method. By default, the value is 0.
        *
        */
        unsigned int nlabels() const;

       /** \brief Get a group label of the last read sequence
        *
        * Get one of the group label specified for the last sequence
        * read by the read() method. The index must be valid.
        *
        */
        const char * label(unsigned int index) const;

       /** \brief Actually clears the memory of the instance
        *
        * Actually frees the memory of the instance. This is useful if
        * a large sequence have been read, in order to really free
        * memory.
        *
        */
        void clear();

      private:

       /** \brief Copy constructor is disabled */
        FastaParser(const FastaParser& src) {}

       /** \brief Copy assignment operator is disabled */
        FastaParser& operator=(const FastaParser& src) { return * this; }

        void _init();
        void _free();
        void _reset_sequence();
        void _name_append(char c);
        void _seq_append(char c);
        void _check();
        void _add_label();
        void _append_last_label(char ch);

        unsigned int _lname;
        unsigned int _lname_r;
        char * _name;
        unsigned int _lseq;
        unsigned int _lseq_r;
        char * _seq;
        unsigned int _nlabels;
        unsigned int _nlabels_r;
        char ** _labels;
        unsigned int * _labels_r;
        unsigned int * _labels_n;

        bool _good;
        std::ifstream _fstream;
        std::istringstream _sstream;
        std::istream* _stream;
        unsigned int _lfname_r;
        char * _fname;
        unsigned int _currline;
        FiniteAlphabet<char> * _alph;
    };

   /** \brief Multi-sequence fasta parser (from file)
    *
    * \ingroup parsers
    *
    * Read fasta-formatted sequence data from a file specified by name.
    * For format specification, see the documentation of the class
    * FastaParser, which is used behind the scenes.
    *
    * Note that, for optimal performance, the read_multi() method of
    * FastaParser requires only one FastaParser instance (the best is
    * to re-use a single DataHolder instance to take advantage of memory
    * caching).
    *
    * \param fname name of the fasta-formatted file to read.
    * \param groups boolean specifying whether group labels should be
    * imported or ignored. If true, group labels are stripped from names.
    * \param dest reference to the instance where to place sequences. If
    * the object already contains sequences, new sequences will be
    * appended to it. In any case, the destination object must always be
    * a non-matrix.
    * \param alph alphabet to use for checking characters.
    *
    * Header: <egglib-cpp/Fasta.hpp>
    *
    */
    void read_fasta_file(const char * fname, bool groups, DataHolder& dest, FiniteAlphabet<char>& alph);

   /** \brief Multi-sequence fasta parser (from string)
    *
    * \ingroup parsers
    *
    * Read fasta-formatted sequence data from a raw string. For format
    * specification, see the documentation of the class FastaParser,
    * which is used behind the scenes.
    *
    * \param str string containing fasta-formatted sequences.
    * \param groups boolean specifying whether group labels should be
    * imported or ignored. If true, group labels are stripped from names.
    * \param dest reference to the instance where to place sequences. If
    * the object already contains sequences, new sequences will be
    * appended to it. In any case, the destination object must always be
    * a non-matrix.
    * \param alph alphabet to use for checking characters.
    *
    * Header: <egglib-cpp/Fasta.hpp>
    *
    */
    void read_fasta_string(const std::string str, bool groups, DataHolder& dest, FiniteAlphabet<char>& alph);

   /** \brief Fasta formatter
    *
    * \ingroup parsers
    *
    * Write genetic data to a file, a string or standard output using
    * the fasta format (formally described in FastaParser). It is
    * required that all exported allele values are exportable as
    * characters (in particular, negative values are never allowed). See
    * the methods documentation for more details, in particular
    * set_mapping() to understand how to map alleles to user-specified
    * characters (such as mapping 0, 1, 2, 3 to *A*, *C*, *G*, *T*, for
    * example).
    *
    * Header: <egglib-cpp/Fasta.hpp>
    *
    */
    class FastaFormatter : public BaseFormatter {

        public:

           /** \brief Constructor
            *
            * Parametrization of the instance can be performed using the
            * setter methods (their names start with *set_*). The
            * default values of the argument of these method represent
            * the default value of the options By default, output is
            * sent to the standard output. A (new) output file can be
            * created at any time using open_file().
            *
            * Concerning the arguments *first* and *last*, please note
            * that sequences will be imported if *last* < *first*, or if
            * *first* is larger than the last index. If *last* is larger
            * than the last index, all last sequences are exported and
            * no error is caused. The default values of *first* and
            * *last* ensure that all sequences are exported.
            *
            */
            FastaFormatter();

           /** \brief Destructor
            *
            * Destroys the object. If an output file is currently open,
            * it is closed at this point.
            *
            */
            virtual ~FastaFormatter();

           /** \brief Sets all parameters to defaults
            *
            */
            void defaults();

           /** \brief Sets index of the first sample to export
            *
            */
            void set_first(unsigned int first = 0);

           /** \brief Sets index of the last sample to export
            *
            */
            void set_last(unsigned int last = MAX);

           /** \brief Specifies whether the group labels should be exported
            *
            */
            void set_labels(bool labels = true);

           /** \brief Sets the length of sequence line.
            *
            * If zero, the whole sequence is written on a single line.
            *
            */
            void set_linelength(unsigned int linelength = 50);

           /** \brief Write fasta-formatted data
            *
            * The parameters specified by the last call to config() (or
            * the defaults) apply). If an output file has be opened with
            * open_file(), data are written into this file. Otherwise, data
            * are written to the standard output.
            *
            */
            void write(const DataHolder& src, AbstractBaseAlphabet& alph);

           /** \brief Write fasta-formatted data to string
            *
            * As to_stream() but generates and and returns a string. If
            * there is an open file, it is not touched.
            *
            */
            std::string write_string(const DataHolder& src, AbstractBaseAlphabet& alph);

        private:
            FastaFormatter(const FastaFormatter& src) {}
            FastaFormatter& operator=(const FastaFormatter& src) { return * this;}

            bool _labels;
            unsigned int _first;
            unsigned int _last;
            unsigned int _linelength;
    };
}

#endif
